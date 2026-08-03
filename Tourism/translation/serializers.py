from rest_framework import serializers


class TranslateRequestSerializer(serializers.Serializer):
    text = serializers.CharField()
    target_language = serializers.CharField(max_length=10)
    source_language = serializers.CharField(max_length=10, required=False, default="auto")
    provider = serializers.ChoiceField(
        choices=["auto", "gemini", "groq", "openai", "standard"], required=False, default="auto"
    )