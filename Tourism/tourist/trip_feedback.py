"""
Tourism/tourist/trip_feedback.py
"""
from rest_framework import permissions, serializers, viewsets

from .models import TripFeedback, TripFeedbackMedia, Itinerary


class TripFeedbackMediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = TripFeedbackMedia
        fields = ["id", "media_type", "file", "caption", "uploaded_at"]


class TripFeedbackSerializer(serializers.ModelSerializer):
    media = TripFeedbackMediaSerializer(many=True, read_only=True)

    class Meta:
        model = TripFeedback
        fields = [
            "id", "itinerary", "num_people",
            "actual_total_cost", "actual_accommodation_cost", "actual_travel_cost",
            "actual_entry_fees_cost", "actual_food_cost", "extra_cost", "extra_cost_note",
            "route_rating", "route_notes", "hotel_rating", "hotel_notes",
            "restaurant_rating", "restaurant_notes", "general_suggestion",
            "media", "created_at",
        ]
        read_only_fields = ["created_at"]

    def validate_itinerary(self, itinerary):
        # Only the itinerary's own owner can leave feedback on it.
        request = self.context.get("request")
        if request and itinerary.user_id != request.user.id:
            raise serializers.ValidationError("You can only leave feedback on your own itineraries.")
        return itinerary


class TripFeedbackViewSet(viewsets.ModelViewSet):
    """
    Standard CRUD, scoped to the user's own feedback. Media (images/
    video) is uploaded via separate calls to /trip-feedback-media/
    after creating the feedback record (standard multi-file-upload
    pattern -- one endpoint for the feedback record, one for each file).
    """
    serializer_class = TripFeedbackSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return TripFeedback.objects.none()
        return TripFeedback.objects.filter(submitted_by=self.request.user).prefetch_related("media")

    def perform_create(self, serializer):
        serializer.save(submitted_by=self.request.user)


class TripFeedbackMediaViewSet(viewsets.ModelViewSet):
    """POST here with {"feedback": <id>, "media_type": "image"|"video", "file": <upload>}"""
    serializer_class = TripFeedbackMediaSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return TripFeedbackMedia.objects.none()
        return TripFeedbackMedia.objects.filter(feedback__submitted_by=self.request.user)