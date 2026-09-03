"""
Serializers for the Local Guide dashboard and Personal Details endpoints
(see views_local.py). Kept separate from serializers.py to avoid touching
that 2000+ line module.
"""
from rest_framework import serializers

from .models import PersonalDetail


class PersonalDetailSerializer(serializers.ModelSerializer):
    fullName = serializers.CharField(source="full_name", max_length=150)
    relationTag = serializers.ChoiceField(
        source="relation_tag", choices=["self", "relative"], default="self"
    )
    idType = serializers.CharField(source="id_type", max_length=50, required=False, allow_blank=True)
    idNumber = serializers.CharField(source="id_number", max_length=100, required=False, allow_blank=True)

    class Meta:
        model = PersonalDetail
        fields = [
            "id",
            "fullName",
            "relationTag",
            "relation",
            "phone",
            "idType",
            "idNumber",
            "nationality",
            "notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
