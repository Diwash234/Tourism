from rest_framework import serializers

from .models import Booking, HotelReview


class BookingSerializer(serializers.ModelSerializer):
    hotel_name = serializers.CharField(source="hotel.name", read_only=True)
    user_email = serializers.CharField(source="user.email", read_only=True)

    class Meta:
        model = Booking
        fields = [
            "id", "user", "user_email", "hotel", "hotel_name", "check_in", "check_out",
            "guests", "status", "total_price", "currency", "special_requests",
            "created_at", "updated_at",
        ]
        read_only_fields = ["user", "status", "total_price", "created_at", "updated_at"]

    def validate(self, attrs):
        check_in = attrs.get("check_in") or getattr(self.instance, "check_in", None)
        check_out = attrs.get("check_out") or getattr(self.instance, "check_out", None)
        if check_in and check_out and check_out <= check_in:
            raise serializers.ValidationError("check_out must be after check_in.")
        return attrs

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)


class BookingStatusUpdateSerializer(serializers.Serializer):
    """Used by hotel admins/super admins to confirm/cancel/complete a booking."""

    status = serializers.ChoiceField(choices=Booking.Status.choices)


class HotelReviewSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source="user.full_name", read_only=True)

    class Meta:
        model = HotelReview
        fields = ["id", "hotel", "user", "user_name", "booking", "rating", "comment", "created_at"]
        read_only_fields = ["user", "created_at"]

    def validate_hotel(self, hotel):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            qs = HotelReview.objects.filter(hotel=hotel, user=request.user)
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError("You have already reviewed this hotel.")
        return hotel

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)