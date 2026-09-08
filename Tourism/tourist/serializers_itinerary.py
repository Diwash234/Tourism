"""
Tourism/tourist/serializers_itinerary.py -- kept separate from the
already-700+-line serializers.py, same reasoning as the family-safety
split earlier this session.
"""
from rest_framework import serializers

from .models import Itinerary, ItineraryDay, ItineraryStop, Destination, Category


class ItineraryStopSerializer(serializers.ModelSerializer):
    destination_name = serializers.CharField(source="destination.name", read_only=True)
    destination_slug = serializers.CharField(source="destination.slug", read_only=True)
    destination_category = serializers.CharField(source="destination.category.name", read_only=True, default=None)

    class Meta:
        model = ItineraryStop
        fields = [
            "id", "destination", "destination_name", "destination_slug", "destination_category",
            "order", "distance_from_previous_km", "notes", "is_visited", "visited_at",
        ]
        read_only_fields = ["distance_from_previous_km", "visited_at"]


class ItineraryDaySerializer(serializers.ModelSerializer):
    stops = ItineraryStopSerializer(many=True, read_only=True)

    class Meta:
        model = ItineraryDay
        fields = ["id", "day_number", "date", "stops"]


class ItinerarySerializer(serializers.ModelSerializer):
    days = ItineraryDaySerializer(many=True, read_only=True)
    progress = serializers.ReadOnlyField()
    category_filter_names = serializers.SlugRelatedField(
        source="category_filter", slug_field="name", many=True, read_only=True
    )

    class Meta:
        model = Itinerary
        fields = [
            "id", "title", "status", "start_date", "num_days", "total_distance_km",
            "category_filter", "category_filter_names", "days", "progress", "created_at",
        ]
        read_only_fields = ["total_distance_km", "created_at"]


class ItineraryCreateSerializer(serializers.Serializer):
    """
    Write-only shape for POST /itineraries/ -- accepts a flat list of
    destination IDs (pre-filtered by the frontend using the existing
    /destinations/?category=X filter -- no new category-filtering logic
    needed server-side, that already works) and a day count. The day-wise
    split + real route distances are computed server-side.
    """
    title = serializers.CharField(required=False, allow_blank=True, default="")
    destination_ids = serializers.ListField(child=serializers.IntegerField(), min_length=1)
    num_days = serializers.IntegerField(min_value=1, max_value=60)
    start_date = serializers.DateField(required=False, allow_null=True)
    category_ids = serializers.ListField(child=serializers.IntegerField(), required=False, default=list)

    def validate_destination_ids(self, value):
        found = set(Destination.objects.filter(id__in=value).values_list("id", flat=True))
        missing = set(value) - found
        if missing:
            raise serializers.ValidationError(f"Destination IDs not found: {sorted(missing)}")
        return value