"""
safety/serializers.py
"""
from rest_framework import serializers

from .models import TrustedContact, SharedTrip, LocationPing, SOSAlert


class TrustedContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrustedContact
        fields = ["id", "name", "relationship", "email", "phone_number", "created_at"]
        read_only_fields = ["id", "created_at"]

    def validate(self, attrs):
        if not attrs.get("email") and not attrs.get("phone_number"):
            raise serializers.ValidationError("Provide at least an email or phone number to reach this contact.")
        return attrs


class LocationPingSerializer(serializers.ModelSerializer):
    class Meta:
        model = LocationPing
        fields = ["id", "latitude", "longitude", "recorded_at"]
        read_only_fields = ["id", "recorded_at"]


class SharedTripSerializer(serializers.ModelSerializer):
    trusted_contacts = TrustedContactSerializer(many=True, read_only=True)
    trusted_contact_ids = serializers.PrimaryKeyRelatedField(
        source="trusted_contacts", queryset=TrustedContact.objects.all(), many=True, write_only=True, required=False,
    )
    latest_ping = serializers.SerializerMethodField()
    is_valid = serializers.SerializerMethodField()

    class Meta:
        model = SharedTrip
        fields = [
            "id", "share_token", "label", "is_active", "started_at", "expires_at",
            "trusted_contacts", "trusted_contact_ids", "latest_ping", "is_valid",
        ]
        read_only_fields = ["id", "share_token", "started_at"]

    def get_latest_ping(self, obj):
        ping = obj.pings.first()  # Meta.ordering = ["-recorded_at"]
        return LocationPingSerializer(ping).data if ping else None

    def get_is_valid(self, obj):
        return obj.is_valid()

    def validate(self, attrs):
        # Every trusted contact tagged on a trip must belong to the same
        # user creating it -- otherwise a user could silently share their
        # live location with someone ELSE's saved contact.
        request = self.context.get("request")
        contacts = attrs.get("trusted_contacts", [])
        if request and contacts:
            for contact in contacts:
                if contact.user_id != request.user.id:
                    raise serializers.ValidationError("One or more contacts don't belong to you.")
        return attrs


class SOSAlertSerializer(serializers.ModelSerializer):
    class Meta:
        model = SOSAlert
        fields = [
            "id", "trip", "latitude", "longitude", "message", "status",
            "triggered_at", "resolved_at", "notified_contacts",
        ]
        read_only_fields = ["id", "triggered_at", "resolved_at", "notified_contacts"]