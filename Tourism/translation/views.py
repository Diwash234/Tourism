import concurrent.futures
import hashlib
import logging

from django.core.cache import cache
from rest_framework import permissions, serializers
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import serializers

from .engine import translate_text
from .serializers import TranslateRequestSerializer

logger = logging.getLogger(__name__)

CACHE_SECONDS = 60 * 60 * 24 * 14
MAX_BATCH_ITEMS = 50
MAX_ITEM_CHARS = 600


def _cache_key(text, target, source):
    return f"tx:{source}:{target}:{hashlib.sha1(text.encode('utf-8')).hexdigest()}"


def cached_translate(text, target, source="auto"):
    """translate_text() with a result cache (one provider call per string per language).

    An answer equal to the input means the provider failed or the string is
    untranslatable (a name, a number): it is returned but NOT cached, so a
    temporary outage cannot freeze English into the cache.
    """
    text = str(text or "")
    if not text.strip():
        return text
    key = _cache_key(text, target, source)
    hit = cache.get(key)
    if hit is not None:
        return hit
    result = translate_text(text, target, source) or text
    if result.strip() and result.strip() != text.strip():
        cache.set(key, result, CACHE_SECONDS)
    return result


class TranslateBatchRequestSerializer(serializers.Serializer):
    texts = serializers.ListField(
        child=serializers.CharField(allow_blank=True, max_length=MAX_ITEM_CHARS),
        allow_empty=False, max_length=MAX_BATCH_ITEMS)
    target_language = serializers.CharField(max_length=10)
    source_language = serializers.CharField(max_length=10, required=False, default="en")


class TranslateBatchView(APIView):
    """POST /api/v1/translate/batch/

    {"texts": ["Hotels", "Budget"], "target_language": "ne", "source_language": "en"}
    -> {"translations": ["होटल", "बजेट"], "target_language": "ne"}

    The page-level translator sends every untranslated visible string of a page
    here. Order is preserved, duplicates are translated once, results are
    cached, and a failed item comes back unchanged (never an error for the page).
    """
    permission_classes = [permissions.AllowAny]
    throttle_scope = None
    # Declared so drf-spectacular can document the batch request body; the view
    # validates with the same serializer instance below.
    serializer_class = TranslateBatchRequestSerializer

    def post(self, request):
        ser = TranslateBatchRequestSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        texts = ser.validated_data["texts"]
        target = ser.validated_data["target_language"]
        source = ser.validated_data["source_language"]
        unique = list(dict.fromkeys(t for t in texts if t.strip()))
        done = {}

        def work(text):
            try:
                return text, cached_translate(text, target, source)
            except Exception:  # noqa: BLE001 - one bad string must not fail the page
                logger.exception("batch translate item failed")
                return text, text

        if unique:
            with concurrent.futures.ThreadPoolExecutor(max_workers=min(6, len(unique))) as pool:
                for text, result in pool.map(work, unique):
                    done[text] = result
        return Response({
            "translations": [done.get(t, t) for t in texts],
            "target_language": target,
        })


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
