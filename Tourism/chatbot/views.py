from rest_framework import permissions, status
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

from ml_service.services.emergency_service import nearest_facilities


class NearbyEmergencyView(APIView):

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


        results = nearest_facilities(
            latitude=lat,
            longitude=lon,
            category=category,
            limit=limit
        )


        return Response({
            "facilities": results
        })



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
        ChatMessage.objects.create(conversation=conversation, role=ChatMessage.Role.USER, content=data["message"])

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
        else:
            reply_text = str(reply_result)
            destination_cards = []
            image_cards = []
            itinerary_cards = None
            distance_cards = None
            emergency_cards = []

        reply = ChatMessage.objects.create(
            conversation=conversation, role=ChatMessage.Role.ASSISTANT, content=reply_text
        )
        conversation.save()  # bumps updated_at via auto_now

        return Response({
            "conversation_id": conversation.id,
            "reply": reply_text,
            "message_id": reply.id,
            "destination_cards": destination_cards,
            "image_cards": image_cards,
            "itinerary_cards": itinerary_cards,
            "distance_cards": distance_cards,
            "emergency_cards": emergency_cards,
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

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        conversations = ChatConversation.objects.filter(user=request.user).prefetch_related("messages")
        return Response(ChatConversationSerializer(conversations, many=True).data)