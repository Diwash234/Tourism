from django.core.cache import cache
from django.db.models import Q
from rest_framework import permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response

from .image_pipeline import resolve_place_image
from .image_acquisition_pipeline import ImageAcquisitionPipeline
from .models import Destination, DestinationImage


def get_destination_by_slug_or_id(val):
    try:
        return Destination.objects.get(id=int(val))
    except (ValueError, Destination.DoesNotExist):
        pass
    try:
        return Destination.objects.get(slug=str(val))
    except Destination.DoesNotExist:
        # try case insensitive match
        first = Destination.objects.filter(Q(slug__iexact=str(val)) | Q(name__iexact=str(val))).first()
        return first


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


class DestinationImagesListView(APIView):
    """
    GET /api/v1/destinations/<slug_or_id>/images
    GET /api/v1/destinations/<slug_or_id>/images/
    Returns full multi-source image collection with complete legal provenance.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request, slug):
        destination = get_destination_by_slug_or_id(slug)
        if not destination:
            return Response({"detail": f"Destination '{slug}' not found."}, status=status.HTTP_404_NOT_FOUND)

        pipeline = ImageAcquisitionPipeline()
        images = pipeline.acquire_images_for_destination(destination, limit=14, force_refresh=False)
        return Response({
            "destination": destination.name,
            "count": len(images),
            "images": images,
        })


class DestinationImagesDiscoverView(APIView):
    """
    POST /api/v1/destinations/<slug_or_id>/images/discover
    POST /api/v1/destinations/<slug_or_id>/images/discover/
    Manually triggers multi-source image discovery across Wikimedia Commons,
    Openverse, Unsplash, Pexels, Flickr, and Pixabay.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request, slug):
        destination = get_destination_by_slug_or_id(slug)
        if not destination:
            return Response({"detail": f"Destination '{slug}' not found."}, status=status.HTTP_404_NOT_FOUND)

        pipeline = ImageAcquisitionPipeline()
        images = pipeline.acquire_images_for_destination(destination, limit=14, force_refresh=False)
        return Response({
            "destination": destination.name,
            "count": len(images),
            "images": images,
            "message": "Multi-source image discovery completed.",
        })


class DestinationImagesRefreshView(APIView):
    """
    POST /api/v1/destinations/<slug_or_id>/images/refresh
    POST /api/v1/destinations/<slug_or_id>/images/refresh/
    Manually triggers force refresh of image collection across all sources.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request, slug):
        destination = get_destination_by_slug_or_id(slug)
        if not destination:
            return Response({"detail": f"Destination '{slug}' not found."}, status=status.HTTP_404_NOT_FOUND)

        pipeline = ImageAcquisitionPipeline()
        images = pipeline.acquire_images_for_destination(destination, limit=14, force_refresh=True)
        return Response({
            "destination": destination.name,
            "count": len(images),
            "images": images,
            "message": "Multi-source image collection refreshed.",
        })


class DestinationImageSetCoverView(APIView):
    """
    POST /api/v1/destinations/<slug>/images/<image_id>/set-cover/

    Sets an existing gallery image as the destination's cover. This is the
    "rollback"/manual-override control: after a refresh or discovery an
    admin can restore any previously-stored image as the cover. Requires
    authentication (any logged-in user can pick; full admin moderation is
    enforced separately in the admin panel).
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, slug, image_id):
        destination = get_destination_by_slug_or_id(slug)
        if not destination:
            return Response({"detail": "Destination not found."}, status=status.HTTP_404_NOT_FOUND)

        image = destination.gallery.filter(id=image_id).first()
        if not image:
            return Response({"detail": "Image not found for this destination."}, status=status.HTTP_404_NOT_FOUND)

        destination.gallery.filter(is_cover=True).exclude(id=image.id).update(is_cover=False)
        image.is_cover = True
        image.save(update_fields=["is_cover"])

        cover_url = image.external_url
        Destination.objects.filter(pk=destination.pk).update(cover_image=cover_url or "")

        return Response({
            "message": "Cover image updated.",
            "destination": destination.name,
            "image_id": image.id,
            "cover_url": cover_url,
        })
