"""
New file: Tourism/tourist/serializers_family_safety.py
(kept separate from the main serializers.py, which is already 700+
lines, rather than growing that file further)
"""
from rest_framework import serializers

from .models import TrustedContact, SharedTrip, LocationPing, SOSAlert, FamilyLink


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

class FamilyLinkSerializer(serializers.ModelSerializer):
    """A family link from the perspective of the requesting user."""

    member_id = serializers.IntegerField(read_only=True)
    member_name = serializers.SerializerMethodField()
    member_username = serializers.SerializerMethodField()
    requester_name = serializers.SerializerMethodField()
    requester_username = serializers.SerializerMethodField()
    direction = serializers.SerializerMethodField()
    username_or_email = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = FamilyLink
        fields = [
            "id", "requester", "member", "member_id", "member_name", "member_username",
            "requester_name", "requester_username", "relationship", "status",
            "direction", "username_or_email", "created_at", "accepted_at",
        ]
        read_only_fields = ["id", "requester", "member", "created_at", "accepted_at"]

    def get_member_name(self, obj):
        u = obj.member
        return (u.first_name or u.full_name or u.email or "").strip() or u.email

    def get_member_username(self, obj):
        return getattr(obj.member, "username", "") or obj.member.email or obj.member.id

    def get_requester_name(self, obj):
        u = obj.requester
        return (u.first_name or u.full_name or u.email or "").strip() or u.email

    def get_requester_username(self, obj):
        return getattr(obj.requester, "username", "") or obj.requester.email or obj.requester.id

    def get_direction(self, obj):
        request = self.context.get("request")
        if request and obj.requester_id == request.user.id:
            return "sent"
        return "received"


class FamilyMemberSerializer(serializers.Serializer):
    """Live status of an accepted family member (for the family dashboard)."""

    link_id = serializers.IntegerField()
    user_id = serializers.IntegerField()
    name = serializers.CharField()
    username = serializers.CharField()
    relationship = serializers.CharField(allow_blank=True)
    is_live = serializers.BooleanField()
    live_trip = serializers.DictField(allow_null=True, required=False)
    latest_ping = serializers.DictField(allow_null=True, required=False)
    history = serializers.ListField(child=serializers.DictField(), required=False)
    active_sos = serializers.ListField(child=serializers.DictField(), required=False)
