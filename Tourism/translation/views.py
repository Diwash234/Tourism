from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import serializers

from .engine import translate_text
from .serializers import TranslateRequestSerializer


class TranslateTextView(APIView):
    """
    POST /api/v1/translate/
    Moved from tourist/views.py -- same path, same response shape.
    """
    permission_classes = [permissions.AllowAny]
    serializer_class = TranslateRequestSerializer

    def post(self, request):
        serializer = TranslateRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        translated = translate_text(
            serializer.validated_data["text"],
            serializer.validated_data["target_language"],
            serializer.validated_data.get("source_language", "auto"),
            serializer.validated_data.get("provider", "auto"),
        )
        return Response({"translated_text": translated, "translatedText": translated})

class TranslateBatchView(APIView):
    """POST /api/v1/translate/batch/ for page-level UI translation."""
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        items = request.data.get("items", [])
        target = request.data.get("target_language", "en")
        source = request.data.get("source_language", "auto")
        provider = request.data.get("provider", "auto")
        if not isinstance(items, list) or len(items) > 100:
            return Response({"detail": "items must be a list of at most 100 strings."}, status=400)
        if not target or target == source:
            return Response({"translations": items})
        translations = []
        for item in items:
            text = str(item or "")
            translations.append(translate_text(text, target, source, provider) or text)
        return Response({"translations": translations})
