from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from .engine import translate_text
from .serializers import TranslateRequestSerializer


class TranslateTextView(APIView):
    """
    POST /api/v1/translate/
    Same path as before the app split -- moved from tourist/views.py,
    URL unchanged so nothing that already calls this needs to change.

    Now also accepts an optional `provider` field ("auto" | "gemini" |
    "groq" | "openai" | "standard") -- previously translate_text()
    supported this param but nothing in the request chain actually
    exposed it to the frontend. translationPreference.js already reads/
    writes a provider preference client-side; this is what lets that
    preference actually reach the translation call.
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