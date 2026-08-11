from django.core.cache import cache
from rest_framework import permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response

from .image_pipeline import resolve_place_image
from .models import Destination, DestinationImage


class ImageResolveView(APIView):
    """
    GET /api/v1/images/resolve/?name=...&lat=...&lon=...&district=...&category=...

    Scalable external place media resolver.
    Returns authentic, location-verified, copyright-safe place photography
    for all 77 districts and 50,000+ candidate places with zero people/portraits.
    Cached for 30 days.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        name = (request.query_params.get("name") or request.query_params.get("query") or "").strip()
        if not name:
            return Response({"detail": "name or query parameter is required."}, status=status.HTTP_400_BAD_REQUEST)

        district = request.query_params.get("district", "").strip()
        province = request.query_params.get("province", "").strip()
        category = request.query_params.get("category", "").strip()

        try:
            lat = float(request.query_params.get("lat") or request.query_params.get("latitude") or 0) or None
            lon = float(request.query_params.get("lon") or request.query_params.get("lng") or request.query_params.get("longitude") or 0) or None
        except (ValueError, TypeError):
            lat, lon = None, None

        cache_key = f"img_res:{name.lower()}:{district.lower()}:{category.lower()}"
        cached = cache.get(cache_key)
        if cached is not None:
            return Response({**cached, "cached": True})

        result = resolve_place_image(
            name=name,
            latitude=lat,
            longitude=lon,
            district=district,
            province=province,
            category=category,
        )

        cache.set(cache_key, result, timeout=60 * 60 * 24 * 30)  # 30 days cache
        return Response({**result, "cached": False})
