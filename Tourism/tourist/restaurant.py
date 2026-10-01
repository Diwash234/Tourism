"""
Tourism/tourist/restaurant.py -- serializers + views for Restaurant, kept
in one file since it's small (unlike Hotel which is spread across the
already-huge serializers.py/views.py). Mirrors HotelSerializer/
HotelViewSet/HotelSearchView exactly -- same image-URL-with-fallback
logic, same search pattern.
"""
from django.db.models import Q
from rest_framework import generics, permissions, serializers, viewsets

from .models import Restaurant
from .permissions import IsAdminOrReadOnly


class RestaurantSerializer(serializers.ModelSerializer):
    """Same shape as the public serializer in serializers.py (which is the one
    the router registers): the model stores a plural `cuisine_types` list and
    an `image_url` column, and rows are located through their destination."""

    image_url = serializers.SerializerMethodField()
    destination_name = serializers.CharField(source="destination.name", read_only=True)

    class Meta:
        model = Restaurant
        fields = [
            "id", "destination", "destination_name", "name", "cuisine_types", "price_range",
            "phone", "opening_hours", "website", "image_url", "vegetarian_friendly",
            "address", "latitude", "longitude", "source_name", "source_url",
            "is_verified", "status", "updated_at",
        ]
        read_only_fields = ["is_verified", "status", "updated_at"]

    def get_image_url(self, obj):
        """Own image first, then the destination's verified cover photo --
        mirrors the public HotelSerializer/RestaurantSerializer fallback."""
        if obj.image_url:
            return obj.image_url
        if obj.destination_id is None:
            return None
        from .serializers import public_destination_cover
        return public_destination_cover(obj.destination, self.context.get("request"))


class RestaurantViewSet(viewsets.ModelViewSet):
    """Public read; admin write -- same access pattern as HotelViewSet."""
    queryset = Restaurant.objects.select_related("destination")
    serializer_class = RestaurantSerializer
    permission_classes = [IsAdminOrReadOnly]
    filterset_fields = ["destination", "cuisine_types", "price_range", "source_name"]
    ordering_fields = ["name", "price_range", "created_at"]
    search_fields = ["name", "address", "cuisine_types"]


class RestaurantSearchView(generics.ListAPIView):
    """
    GET /api/v1/restaurants/search/?query=Pokhara
    GET /api/v1/restaurants/search/?query=Newari
    Same text-search pattern as HotelSearchView -- searches name,
    destination, address, and cuisine type.
    """
    serializer_class = RestaurantSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        query = self.request.query_params.get("query", "").strip()
        if not query:
            return Restaurant.objects.none()
        return Restaurant.objects.filter(
            Q(name__icontains=query)
            | Q(destination__name__icontains=query)
            | Q(destination__city__icontains=query)
            | Q(cuisine_types__icontains=query)
            | Q(address__icontains=query),
            status="published",
        ).select_related("destination")[:20]