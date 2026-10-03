import logging

from rest_framework import permissions, status

logger = logging.getLogger(__name__)
from rest_framework.response import Response
from rest_framework.views import APIView
import sys
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

sys.path.append(os.path.dirname(BASE_DIR))

from .models import ChatConversation, ChatMessage
from .serializers import ChatConversationSerializer, ChatSendMessageSerializer
from .services import get_chatbot_reply

from rest_framework.permissions import AllowAny

import math
import csv

def _haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    phi1, phi2 = math.radians(float(lat1)), math.radians(float(lat2))
    dphi = math.radians(float(lat2) - float(lat1))
    dlambda = math.radians(float(lon2) - float(lon1))
    a = math.sin(dphi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2.0) ** 2
    return R * 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))

def get_nearest_facilities(latitude, longitude, category=None, limit=5):
    from tourist.models import Hospital, PoliceStation
    results = []

    want_hospitals = not category or category in ("hospital", "hospitals")
    want_police = not category or category in ("police", "police_station", "police_stations")

    if want_hospitals:
        for h in Hospital.objects.all()[:300]:
            try:
                dist = _haversine_km(latitude, longitude, h.latitude, h.longitude)
                results.append({
                    "type": "hospital",
                    "name": h.name,
                    "phone": h.phone or "",
                    "address": h.address or "",
                    "district": h.district or "",
                    "province": getattr(h.destination, "province", "") if h.destination else "",
                    "latitude": float(h.latitude),
                    "longitude": float(h.longitude),
                    "distance_km": round(dist, 2),
                })
            except Exception:
                continue

    if want_police:
        for p in PoliceStation.objects.all()[:300]:
            try:
                dist = _haversine_km(latitude, longitude, p.latitude, p.longitude)
                results.append({
                    "type": "police_station",
                    "name": p.name,
                    "phone": p.phone or "",
                    "address": p.address or "",
                    "district": getattr(p, "district", "") or (p.destination.district if p.destination else ""),
                    "province": getattr(p.destination, "province", "") if p.destination else "",
                    "latitude": float(p.latitude),
                    "longitude": float(p.longitude),
                    "distance_km": round(dist, 2),
                })
            except Exception:
                continue

    # Fallback to CSV datasets if database has no records
    if not results:
        dataset_dir = os.path.join(BASE_DIR, "dataset")
        if want_hospitals:
            csv_path = os.path.join(dataset_dir, "hospital_cleaned.csv")
            if os.path.exists(csv_path):
                try:
                    with open(csv_path, mode="r", encoding="utf-8") as f:
                        reader = csv.DictReader(f)
                        for row in reader:
                            try:
                                lat = float(row.get("latitude") or 0)
                                lon = float(row.get("longitude") or 0)
                                if lat and lon:
                                    dist = _haversine_km(latitude, longitude, lat, lon)
                                    results.append({
                                        "type": "hospital",
                                        "name": row.get("hospital_name") or row.get("name") or "Unknown Hospital",
                                        "phone": row.get("phone", ""),
                                        "address": row.get("address", ""),
                                        "district": row.get("district", ""),
                                        "province": row.get("province", ""),
                                        "latitude": lat,
                                        "longitude": lon,
                                        "distance_km": round(dist, 2),
                                    })
                            except (ValueError, TypeError):
                                continue
                except Exception:
                    pass

        if want_police:
            csv_path = os.path.join(dataset_dir, "police_station_cleaned.csv")
            if not os.path.exists(csv_path):
                csv_path = os.path.join(dataset_dir, "nearbypolice.csv")
            if os.path.exists(csv_path):
                try:
                    with open(csv_path, mode="r", encoding="utf-8") as f:
                        reader = csv.DictReader(f)
                        for row in reader:
                            try:
                                lat = float(row.get("latitude") or 0)
                                lon = float(row.get("longitude") or 0)
                                if lat and lon:
                                    dist = _haversine_km(latitude, longitude, lat, lon)
                                    results.append({
                                        "type": "police_station",
                                        "name": row.get("police_station") or row.get("name") or "Unknown Police Station",
                                        "phone": row.get("phone", ""),
                                        "address": row.get("address", ""),
                                        "district": row.get("district", ""),
                                        "province": row.get("province", ""),
                                        "latitude": lat,
                                        "longitude": lon,
                                        "distance_km": round(dist, 2),
                                    })
                            except (ValueError, TypeError):
                                continue
                except Exception:
                    pass

    results.sort(key=lambda x: x["distance_km"])
    return results[:limit]


class NearbyEmergencyView(APIView):
    serializer_class = None

    permission_classes = [AllowAny]


    def get(self, request):

        try:
            lat = float(request.GET.get("latitude"))
            lon = float(request.GET.get("longitude"))
        except (TypeError, ValueError):
            return Response(
                {"detail": "latitude and longitude query parameters are required and must be numbers."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        category = request.GET.get("category")

        try:
            limit = int(
                request.GET.get(
                    "limit",
                    5
                )
            )
        except (TypeError, ValueError):
            limit = 5


        results = get_nearest_facilities(
            latitude=lat,
            longitude=lon,
            category=category,
            limit=limit
        )


        return Response({
            "facilities": results
        })



def _broadcast(conversation_id, payload):
    """Push a persisted chat event to every WebSocket in the conversation.

    Best-effort by design: chat rendering must never depend on the socket
    layer being reachable (spec: the chatbot must not block the site).
    """
    try:
        import asyncio

        from channels.layers import get_channel_layer

        from .consumers import get_main_loop

        layer = get_channel_layer()
        if layer is None:
            return
        group = f"chat_{conversation_id}"
        event = {"type": "chat.message", "payload": payload}
        main_loop = get_main_loop()
        try:
            running = asyncio.get_running_loop()
        except RuntimeError:
            running = None
        if main_loop is not None and main_loop.is_running() and main_loop is not running:
            # Consumers live on the server's main loop; hand the coroutine to
            # it thread-safely (in-memory layer queues are bound to that loop).
            asyncio.run_coroutine_threadsafe(layer.group_send(group, event), main_loop)
        else:
            from asgiref.sync import async_to_sync

            async_to_sync(layer.group_send)(group, event)
    except Exception:  # pragma: no cover - socket push is optional
        logger.warning("chat websocket broadcast skipped for conversation %s", conversation_id)


class ChatMessageView(APIView):
    """
    POST /api/v1/chatbot/message/  { conversation_id?, message }
    Sends a message, gets an assistant reply, and persists both. Works for
    logged-in users (tied to their account) and anonymous visitors (tied
    to the Django session).
    """

    permission_classes = [permissions.AllowAny]
    serializer_class = ChatSendMessageSerializer

    def post(self, request):
        serializer = ChatSendMessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        latitude = data.get("latitude")
        longitude = data.get("longitude")


        conversation = self._get_or_create_conversation(request, data.get("conversation_id"))
        user_msg = ChatMessage.objects.create(conversation=conversation, role=ChatMessage.Role.USER, content=data["message"])
        _broadcast(conversation.id, {
            "type": "user_message", "conversation_id": conversation.id,
            "message_id": user_msg.id, "content": user_msg.content,
        })

        history = [
            {"role": m.role, "content": m.content}
            for m in conversation.messages.order_by("created_at")
        ]
        
        reply_result = get_chatbot_reply(
            history,
            latitude=latitude,
            longitude=longitude
        )

        if isinstance(reply_result, dict):
            reply_text = reply_result.get("reply", "")
            destination_cards = reply_result.get("destination_cards", [])
            image_cards = reply_result.get("image_cards", [])
            itinerary_cards = reply_result.get("itinerary_cards")
            distance_cards = reply_result.get("distance_cards")
            emergency_cards = reply_result.get("emergency_cards", [])
            package_cards = reply_result.get("package_cards", [])
        else:
            reply_text = str(reply_result)
            destination_cards = []
            image_cards = []
            itinerary_cards = None
            distance_cards = None
            emergency_cards = []
            package_cards = []

        reply = ChatMessage.objects.create(
            conversation=conversation, role=ChatMessage.Role.ASSISTANT, content=reply_text
        )
        conversation.save()  # bumps updated_at via auto_now
        _broadcast(conversation.id, {
            "type": "bot_reply", "conversation_id": conversation.id,
            "message_id": reply.id, "reply": reply_text,
            "destination_cards": destination_cards, "image_cards": image_cards,
            "itinerary_cards": itinerary_cards, "distance_cards": distance_cards,
            "emergency_cards": emergency_cards, "package_cards": package_cards,
        })

        return Response({
            "conversation_id": conversation.id,
            "reply": reply_text,
            "message_id": reply.id,
            "destination_cards": destination_cards,
            "image_cards": image_cards,
            "itinerary_cards": itinerary_cards,
            "distance_cards": distance_cards,
            "emergency_cards": emergency_cards,
            "package_cards": package_cards,
        })

    def _get_or_create_conversation(self, request, conversation_id):
        if conversation_id:
            qs = ChatConversation.objects.filter(id=conversation_id)
            if request.user.is_authenticated:
                qs = qs.filter(user=request.user)
            else:
                qs = qs.filter(session_key=request.session.session_key)
            conversation = qs.first()
            if conversation:
                return conversation

        if not request.session.session_key:
            request.session.create()

        return ChatConversation.objects.create(
            user=request.user if request.user.is_authenticated else None,
            session_key="" if request.user.is_authenticated else request.session.session_key,
        )


class ChatHistoryView(APIView):
    """GET /api/v1/chatbot/history/ — the logged-in user's past conversations."""
    serializer_class = None

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        conversations = ChatConversation.objects.filter(user=request.user).prefetch_related("messages")
        return Response(ChatConversationSerializer(conversations, many=True).data)