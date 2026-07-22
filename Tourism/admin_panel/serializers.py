from rest_framework import serializers

from .models import HotelAssignment, AdminTask


class HotelAssignmentSerializer(serializers.ModelSerializer):
    hotel_name = serializers.CharField(source="hotel.name", read_only=True)
    admin_email = serializers.CharField(source="admin.email", read_only=True)

    class Meta:
        model = HotelAssignment
        fields = ["id", "hotel", "hotel_name", "admin", "admin_email", "assigned_by", "assigned_at", "notes"]
        read_only_fields = ["assigned_by", "assigned_at"]

    def create(self, validated_data):
        validated_data["assigned_by"] = self.context["request"].user
        return super().create(validated_data)


class AdminTaskSerializer(serializers.ModelSerializer):
    assigned_to_email = serializers.CharField(source="assigned_to.email", read_only=True)
    assigned_by_email = serializers.CharField(source="assigned_by.email", read_only=True)
    hotel_name = serializers.CharField(source="related_hotel.name", read_only=True)

    class Meta:
        model = AdminTask
        fields = [
            "id", "title", "description", "assigned_to", "assigned_to_email",
            "assigned_by", "assigned_by_email", "related_hotel", "hotel_name",
            "status", "priority", "due_date", "created_at", "updated_at", "completed_at",
        ]
        read_only_fields = ["assigned_by", "created_at", "updated_at", "completed_at"]

    def create(self, validated_data):
        validated_data["assigned_by"] = self.context["request"].user
        return super().create(validated_data)