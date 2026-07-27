from rest_framework import serializers

from .models import ChatConversation, ChatMessage


class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = ["id", "role", "content", "created_at"]


class ChatConversationSerializer(serializers.ModelSerializer):
    messages = ChatMessageSerializer(many=True, read_only=True)

    class Meta:
        model = ChatConversation
        fields = ["id", "created_at", "updated_at", "messages"]


class ChatSendMessageSerializer(serializers.Serializer):

    message = serializers.CharField()

    conversation_id = serializers.IntegerField(
        required=False,
        allow_null=True
    )

    latitude = serializers.FloatField(
        required=False,
        allow_null=True
    )

    longitude = serializers.FloatField(
        required=False,
        allow_null=True
    )
