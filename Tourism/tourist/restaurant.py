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
    image_url = serializers.SerializerMethodField()
    destination_name = serializers.CharField(source="destination.name", read_only=True)

    class Meta:
        model = Restaurant
        fields = [
            "id", "destination", "destination_name", "name", "cuisine_type", "price_range",
            "rating", "phone", "opening_hours", "booking_url", "image_url", "dietary_options",
            "address", "latitude", "longitude", "source",
        ]

    def get_image_url(self, obj):
        """Same pattern as HotelSerializer.get_image_url -- own image first, destination photo as fallback."""
        request = self.context.get("request")

        if obj.cover_image:
            return request.build_absolute_uri(obj.cover_image.url) if request else obj.cover_image.url
        if obj.external_image_url:
            return obj.external_image_url

        if obj.destination and obj.destination.cover_image:
            url = obj.destination.cover_image.url
            return request.build_absolute_uri(url) if request else url

        if obj.destination:
            photo = obj.destination.gallery.filter(is_cover=True).first()
            if photo:
                return photo.external_url

        return None


class RestaurantViewSet(viewsets.ModelViewSet):
    """Public read; admin write -- same access pattern as HotelViewSet."""
    queryset = Restaurant.objects.select_related("destination")
    serializer_class = RestaurantSerializer
    permission_classes = [IsAdminOrReadOnly]
    filterset_fields = ["destination", "cuisine_type", "price_range", "source"]
    ordering_fields = ["rating", "name"]
    search_fields = ["name", "address", "cuisine_type"]


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
            | Q(cuisine_type__icontains=query)
            | Q(address__icontains=query)
        ).select_related("destination")[:20]