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



def _broadcast(conversation_id, payload, group=None):
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
        group = group or f"chat_{conversation_id}"
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
        # Live support inbox: fan the same persisted message out to admins
        # (support_inbox WS group) so staff see it within seconds.
        _broadcast("support_inbox", {
            "type": "support.user_message", "conversation_id": conversation.id,
            "message_id": user_msg.id, "content": user_msg.content,
            "user_email": conversation.user.email if conversation.user else (conversation.session_key or "anonymous"),
        }, group="support_inbox")

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

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        conversations = ChatConversation.objects.filter(user=request.user).prefetch_related("messages")
        return Response(ChatConversationSerializer(conversations, many=True).data)

# ---------------------------------------------------------------------------
# Human support workflow (V6): admin inbox, replies, assignment
# ---------------------------------------------------------------------------
_INBOX_ROLES = {"admin", "super_admin", "tourism_admin", "content_moderator", "staff"}
_ASSIGNABLE_ROLES = _INBOX_ROLES | {"guide"}


def _is_support_staff(user):
    """Can access the support inbox / reply: admins, moderators and staff."""
    return bool(user and getattr(user, "is_authenticated", False) and (
        user.is_staff or getattr(user, "role", "") in _INBOX_ROLES
    ))


def _can_be_assigned(user):
    """Valid assignee: staff/moderator/admin OR a local guide (per V6:
    admins can hand a conversation to a staff member or a guide)."""
    return bool(user and getattr(user, "is_authenticated", False) and (
        user.is_staff or getattr(user, "role", "") in _ASSIGNABLE_ROLES
    ))


class SupportInboxView(APIView):
    """GET /api/v1/chatbot/support/inbox/ — staff only.
    Lists chat conversations with last message + assignment state."""

    def get(self, request):
        if not _is_support_staff(request.user):
            return Response({"detail": "Staff access required."}, status=403)
        from django.db.models import OuterRef, Subquery
        last = ChatMessage.objects.filter(conversation=OuterRef("pk")).order_by("-created_at")
        qs = (ChatConversation.objects
              .annotate(last_content=Subquery(last.values("content")[:1]),
                        last_role=Subquery(last.values("role")[:1]),
                        last_at=Subquery(last.values("created_at")[:1])))
        mine = request.query_params.get("mine") == "1"
        if mine:
            qs = qs.filter(assigned_to=request.user)
        qs = qs.order_by("-updated_at")[:100]
        rows = [{
            "id": c.id,
            "user_email": c.user.email if c.user else (c.session_key or "anonymous"),
            "status": c.status,
            "assigned_to": c.assigned_to.email if c.assigned_to else None,
            "last_message": (c.last_content or "")[:120],
            "last_role": c.last_role,
            "last_at": c.last_at.isoformat() if c.last_at else None,
            "updated_at": c.updated_at.isoformat(),
        } for c in qs]
        return Response({"results": rows})


class SupportThreadView(APIView):
    """GET /api/v1/chatbot/support/thread/<id>/ — staff only. Full message list."""

    def get(self, request, conversation_id):
        if not _is_support_staff(request.user):
            return Response({"detail": "Staff access required."}, status=403)
        conv = ChatConversation.objects.filter(pk=conversation_id).first()
        if conv is None:
            return Response({"detail": "Conversation not found."}, status=404)
        recent = list(conv.messages.order_by("-created_at")[:200])[::-1]
        msgs = [{"id": m.id, "role": m.role, "content": m.content,
                 "created_at": m.created_at.isoformat()}
                for m in recent]
        return Response({"conversation_id": conv.id, "status": conv.status,
                         "assigned_to": conv.assigned_to.email if conv.assigned_to else None,
                         "messages": msgs})


class SupportReplyView(APIView):
    """POST /api/v1/chatbot/support/reply/ {conversation_id, content} — staff only.
    Persists an admin reply and pushes it live to the user's chat socket."""

    def post(self, request):
        if not _is_support_staff(request.user):
            return Response({"detail": "Staff access required."}, status=403)
        cid = request.data.get("conversation_id")
        content = (request.data.get("content") or "").strip()
        if not cid or not content:
            return Response({"detail": "conversation_id and content are required."}, status=400)
        conv = ChatConversation.objects.filter(pk=cid).first()
        if conv is None:
            return Response({"detail": "Conversation not found."}, status=404)
        msg = ChatMessage.objects.create(conversation=conv, role=ChatMessage.Role.ADMIN, content=content)
        conv.save()
        _broadcast(conv.id, {
            "type": "admin_reply", "conversation_id": conv.id,
            "message_id": msg.id, "reply": content,
        })
        return Response({"message_id": msg.id, "conversation_id": conv.id}, status=201)


class SupportAssignView(APIView):
    """POST /api/v1/chatbot/support/assign/ {conversation_id, assigned_to?, status?}.
    Admins can pick up (self-assign), assign to another staff/guide account,
    or resolve. Assigning to a non-staff account is rejected — support work
    stays with verified staff identities."""

    def post(self, request):
        if not _is_support_staff(request.user):
            return Response({"detail": "Staff access required."}, status=403)
        from django.contrib.auth import get_user_model
        cid = request.data.get("conversation_id")
        conv = ChatConversation.objects.filter(pk=cid).first()
        if conv is None:
            return Response({"detail": "Conversation not found."}, status=404)
        status_val = request.data.get("status")
        if status_val:
            if status_val not in ChatConversation.Status.values:
                return Response({"detail": "Invalid status."}, status=400)
            conv.status = status_val
        target_email = request.data.get("assigned_to")
        if target_email == "me":
            conv.assigned_to = request.user
            conv.status = ChatConversation.Status.ASSIGNED
        elif target_email:
            U = get_user_model()
            target = U.objects.filter(email__iexact=target_email).first()
            if target is None or not _can_be_assigned(target):
                return Response({"detail": "Assign only to an existing staff or guide account."}, status=400)
            conv.assigned_to = target
            conv.status = ChatConversation.Status.ASSIGNED
        elif "assigned_to" in request.data:
            conv.assigned_to = None
            if conv.status == ChatConversation.Status.ASSIGNED:
                conv.status = ChatConversation.Status.OPEN
        conv.save()
        _broadcast("support_inbox", {
            "type": "support.assigned", "conversation_id": conv.id,
            "assigned_to": conv.assigned_to.email if conv.assigned_to else None,
            "status": conv.status,
        }, group="support_inbox")
        return Response({"conversation_id": conv.id, "status": conv.status,
                         "assigned_to": conv.assigned_to.email if conv.assigned_to else None})
