from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import ChatConversation, ChatMessage
from .serializers import ChatConversationSerializer, ChatSendMessageSerializer
from .services import get_chatbot_reply


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

        conversation = self._get_or_create_conversation(request, data.get("conversation_id"))
        ChatMessage.objects.create(conversation=conversation, role=ChatMessage.Role.USER, content=data["message"])

        history = [
            {"role": m.role, "content": m.content}
            for m in conversation.messages.order_by("created_at")
        ]
        reply_text = get_chatbot_reply(history)

        reply = ChatMessage.objects.create(
            conversation=conversation, role=ChatMessage.Role.ASSISTANT, content=reply_text
        )
        conversation.save()  # bumps updated_at via auto_now

        return Response({
            "conversation_id": conversation.id,
            "reply": reply_text,
            "message_id": reply.id,
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