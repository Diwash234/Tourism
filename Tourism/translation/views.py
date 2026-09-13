from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

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