import logging
import concurrent.futures

from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import serializers

from .engine import translate_text
from .serializers import TranslateRequestSerializer

logger = logging.getLogger(__name__)


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

    # translate_text() may make several network calls per item (tiered
    # provider fallback), so a 100-item batch done sequentially easily
    # exceeded the frontend's axios timeout and the caller kept the whole
    # page in English. Eight workers keeps a full batch comfortably inside
    # the timeout without hammering the upstream translation services.
    MAX_WORKERS = 8

    def post(self, request):
        items = request.data.get("items", [])
        target = request.data.get("target_language", "en")
        source = request.data.get("source_language", "auto")
        provider = request.data.get("provider", "auto")
        if not isinstance(items, list) or len(items) > 100:
            return Response({"detail": "items must be a list of at most 100 strings."}, status=400)
        if not target or target == source:
            return Response({"translations": items})

        def translate_one(item):
            text = str(item or "")
            try:
                return translate_text(text, target, source, provider) or text
            except Exception:  # noqa: BLE001 - one bad string must not fail the batch
                logger.exception("Batch translation failed for %r; keeping original text", text[:80])
                return text

        if len(items) <= 1:
            translations = [translate_one(item) for item in items]
        else:
            with concurrent.futures.ThreadPoolExecutor(max_workers=min(self.MAX_WORKERS, len(items))) as pool:
                translations = list(pool.map(translate_one, items))
        return Response({"translations": translations})
