from django.core.cache import cache
from rest_framework import permissions
from rest_framework.views import APIView
from rest_framework.response import Response

from .engine import resolve_place_image


class ImageResolveView(APIView):
    """
    GET /api/v1/images/resolve/?query=Ruru+Kshetra

    The image proxy -- the frontend calls THIS, never Unsplash/Pexels/
    Pixabay/Openverse/Wikimedia directly, so API keys stay server-side
    and every result has already passed the relevance check in
    image_pipeline.py. Cached for 7 days per query.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        query = request.query_params.get("query", "").strip()
        if not query:
            return Response({"detail": "query parameter is required."}, status=400)

        cache_key = f"image_resolve:{query.lower()}"
        cached = cache.get(cache_key)
        if cached is not None:
            return Response({**cached, "cached": True})

        result = resolve_place_image(query)
        if result is None:
            return Response(
                {"detail": f"No verified image found for {query!r}.", "url": None},
                status=404,
            )

        cache.set(cache_key, result, timeout=60 * 60 * 24 * 7)  # 7 days
        return Response({**result, "cached": False})