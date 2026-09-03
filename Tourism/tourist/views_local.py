"""
Local Guide Dashboard + Personal Details endpoints.

These close the last three frontend->backend gaps found by auditing every
axios call in frontend/Tourism/src/api against the OpenAPI schema:

  1. /local/places            -- Local Guide Dashboard place submissions.
                                  Creates Destination rows with status=PENDING
                                  so the existing admin pending-places approval
                                  pipeline (/admin/pending-places/) picks them
                                  up. Previously the frontend silently fell
                                  back to localStorage and submissions never
                                  reached an admin.

  2. /user/personal-details   -- traveller document/emergency-contact CRUD
                                  (PersonalDetails.jsx). Previously localStorage
                                  only, so details were lost across devices.

  3. /safety/shared/<token>/  -- public shared-trip view alias (the backend
                                  only exposed /safety/trip-share/<token>/,
                                  while every share link the frontend copies
                                  points at /safety/shared/<token>).
                                  Wired as a URL alias in urls.py.
"""
from django.db import transaction
from rest_framework import permissions, status, viewsets
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Category, Destination, DestinationImage, PersonalDetail
from .permissions import IsOwner
from .serializers_local import PersonalDetailSerializer

# ---------------------------------------------------------------------------
# /local/places -- Local Guide submissions into the admin approval pipeline

HERITAGE_CATEGORY_NAMES = {
    "unesco": "UNESCO World Heritage",
    "religious": "Temple / Religious Site",
    "palace": "Palace / Durbar Square",
    "monastery": "Monastery / Gumba",
    "village": "Traditional Village",
}


def _resolve_category(raw):
    """Map the dashboard's heritage category value to a Category row."""
    if not raw:
        return None
    name = HERITAGE_CATEGORY_NAMES.get(str(raw).strip().lower(), str(raw).strip())
    category = Category.objects.filter(name__iexact=name).first()
    if category is None:
        from django.utils.text import slugify

        category = Category.objects.create(name=name, slug=slugify(name))
    return category


def _serialize_place(place):
    cover = place.gallery.order_by("-is_cover", "-created_at").first()
    image_url = None
    if place.cover_image:
        image_url = place.cover_image.url
    elif cover is not None:
        image_url = cover.image.url if cover.image else cover.external_url
    return {
        "id": place.id,
        "name": place.name,
        "location": place.address or place.city or "",
        "category": place.category.name if place.category else "",
        "description": place.description or "",
        "image": image_url,
        "status": place.status,
        "created_at": place.created_at,
    }


class LocalPlaceSubmissionView(APIView):
    """
    GET  /local/places          -> {"items": [...]}   (own submissions)
    POST /local/places          -> create a PENDING Destination submission
    PUT  /local/places/{id}     -> edit own PENDING submission
    DEL  /local/places/{id}     -> withdraw own submission
    """

    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [JSONParser, FormParser, MultiPartParser]

    def get(self, request):
        places = (
            Destination.objects.filter(created_by=request.user, is_user_submitted=True)
            .select_related("category")
            .order_by("-created_at")
        )
        return Response({"items": [_serialize_place(p) for p in places]})

    def post(self, request):
        data = request.data
        name = (data.get("name") or "").strip()
        if not name:
            return Response({"detail": "Place name is required."}, status=status.HTTP_400_BAD_REQUEST)

        image_url = (data.get("imageUrl") or data.get("image") or "").strip()
        if image_url and not str(image_url).startswith(("http://", "https://")):
            image_url = ""

        with transaction.atomic():
            place = Destination.objects.create(
                name=name,
                address=(data.get("location") or "").strip() or None,
                category=_resolve_category(data.get("category")),
                description=(data.get("description") or "").strip(),
                short_description=(data.get("description") or "").strip()[:180],
                status=Destination.SubmissionStatus.PENDING,
                is_user_submitted=True,
                is_active=False,
                created_by=request.user,
            )
            if image_url:
                DestinationImage.objects.create(
                    destination=place,
                    external_url=image_url,
                    source=DestinationImage.Source.USER_UPLOAD, uploaded_by=request.user,
                    verification_status=DestinationImage.ImageStatus.PENDING,
                )

        return Response(_serialize_place(place), status=status.HTTP_201_CREATED)

    def _get_own_place(self, request, pk):
        place = Destination.objects.filter(pk=pk, created_by=request.user, is_user_submitted=True).first()
        return place

    def put(self, request, pk):
        place = self._get_own_place(request, pk)
        if place is None:
            return Response({"detail": "Place not found."}, status=status.HTTP_404_NOT_FOUND)
        if place.status != Destination.SubmissionStatus.PENDING:
            return Response(
                {"detail": "Only pending submissions can be edited."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        data = request.data
        if data.get("name"):
            place.name = data["name"].strip()
        if "location" in data:
            place.address = (data.get("location") or "").strip() or None
        if data.get("category"):
            place.category = _resolve_category(data["category"])
        if "description" in data:
            place.description = (data.get("description") or "").strip()
            place.short_description = place.description[:180]
        place.save()
        return Response(_serialize_place(place))

    def delete(self, request, pk):
        place = self._get_own_place(request, pk)
        if place is None:
            return Response({"detail": "Place not found."}, status=status.HTTP_404_NOT_FOUND)
        place.delete()
        return Response({"success": True}, status=status.HTTP_200_OK)


class LocalPlaceImageView(APIView):
    """
    POST /local/places/{id}/images  (multipart "image" file)
    Attach a photo to an own PENDING submission. Returns {"success", "url"}.
    """

    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [FormParser, MultiPartParser]

    def post(self, request, pk):
        place = Destination.objects.filter(
            pk=pk, created_by=request.user, is_user_submitted=True
        ).first()
        if place is None:
            return Response({"detail": "Place not found."}, status=status.HTTP_404_NOT_FOUND)

        upload = request.FILES.get("image") or request.FILES.get("file")
        image_url = (request.data.get("imageUrl") or "").strip()
        if upload is None and not image_url:
            return Response({"detail": "An image file or imageUrl is required."}, status=400)

        photo = DestinationImage.objects.create(
            destination=place,
            image=upload or None,
            external_url=image_url if not upload else "",
            source=DestinationImage.Source.USER_UPLOAD, uploaded_by=request.user,
            verification_status=DestinationImage.ImageStatus.PENDING,
        )
        url = photo.image.url if photo.image else photo.external_url
        return Response({"success": True, "url": url, "id": photo.id}, status=status.HTTP_201_CREATED)


# ---------------------------------------------------------------------------
# /user/personal-details -- traveller documents & emergency contacts

class PersonalDetailViewSet(viewsets.ModelViewSet):
    """
    CRUD for the signed-in user's own travel documents / emergency
    contact details (PersonalDetails.jsx). Owner-scoped; responses are
    wrapped as {"items": [...]} on list to match the frontend contract.
    """

    serializer_class = PersonalDetailSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]
    parser_classes = [JSONParser, FormParser, MultiPartParser]

    def get_queryset(self):
        return PersonalDetail.objects.filter(user=self.request.user).order_by("-created_at")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def list(self, request, *args, **kwargs):
        qs = self.get_queryset()
        serializer = self.get_serializer(qs, many=True)
        return Response({"items": serializer.data})
