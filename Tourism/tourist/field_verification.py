"""
Tourism/tourist/field_verification.py -- kept in one file since it's a
self-contained workflow (assign -> submit -> review), same reasoning as
restaurant.py.
"""
from django.utils import timezone
from rest_framework import permissions, serializers, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import FieldVerificationTask, FieldVerificationReport, FieldVerificationPhoto, User
from .permissions import IsRoleOrAbove


class FieldVerificationPhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = FieldVerificationPhoto
        fields = ["id", "image", "caption", "uploaded_at"]


class FieldVerificationReportSerializer(serializers.ModelSerializer):
    photos = FieldVerificationPhotoSerializer(many=True, read_only=True)
    submitted_by_name = serializers.CharField(source="submitted_by.first_name", read_only=True)

    class Meta:
        model = FieldVerificationReport
        fields = [
            "id", "task", "submitted_by", "submitted_by_name", "visit_date",
            "is_place_accurate", "accuracy_notes",
            "witnessed_sickness", "witnessed_accident", "witnessed_misleading_activity",
            "hazards_observed", "transport_ease", "local_helpfulness", "local_behavior_notes",
            "general_notes", "review_status", "reviewed_by", "review_note", "photos", "created_at",
        ]
        read_only_fields = ["submitted_by", "review_status", "reviewed_by", "review_note"]


class FieldVerificationTaskSerializer(serializers.ModelSerializer):
    destination_name = serializers.CharField(source="destination.name", read_only=True)
    assigned_to_name = serializers.CharField(source="assigned_to.first_name", read_only=True)
    report = FieldVerificationReportSerializer(read_only=True)

    class Meta:
        model = FieldVerificationTask
        fields = [
            "id", "destination", "destination_name", "assigned_to", "assigned_to_name",
            "assigned_by", "status", "due_date", "instructions", "report", "created_at",
        ]
        read_only_fields = ["assigned_by", "status"]


class FieldVerificationTaskViewSet(viewsets.ModelViewSet):
    """
    Admin/Tourism-Admin+ create and assign tasks. A FIELD_VERIFIER sees
    only their own assigned tasks and can submit a report against one;
    reviewing a submitted report is separate (the `review` action below,
    Content-Moderator+ only).
    """
    serializer_class = FieldVerificationTaskSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = FieldVerificationTask.objects.select_related("destination", "assigned_to", "report")
        if user.role in (User.Role.ADMIN, User.Role.SUPER_ADMIN, User.Role.TOURISM_ADMIN, User.Role.CONTENT_MODERATOR):
            return qs
        return qs.filter(assigned_to=user)

    def get_permissions(self):
        if self.action == "create":
            return [IsRoleOrAbove(User.Role.TOURISM_ADMIN)]
        return super().get_permissions()

    def perform_create(self, serializer):
        serializer.save(assigned_by=self.request.user)

    @action(detail=True, methods=["post"])
    def submit_report(self, request, pk=None):
        """
        POST /field-verification-tasks/{id}/submit-report/
        Only the assigned field verifier can submit against their own
        task. Creates the report + marks the task submitted.
        """
        task = self.get_object()
        if task.assigned_to_id != request.user.id:
            return Response({"detail": "This task isn't assigned to you."}, status=403)
        if hasattr(task, "report"):
            return Response({"detail": "A report has already been submitted for this task."}, status=400)

        serializer = FieldVerificationReportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(task=task, submitted_by=request.user)

        task.status = FieldVerificationTask.Status.SUBMITTED
        task.save(update_fields=["status"])

        return Response(FieldVerificationTaskSerializer(task).data, status=201)

    @action(detail=True, methods=["post"], permission_classes=[IsRoleOrAbove(User.Role.CONTENT_MODERATOR)])
    def review(self, request, pk=None):
        """
        POST /field-verification-tasks/{id}/review/
        {"decision": "approved" | "rejected", "note": "..."}
        If approved AND the report flagged the listing as inaccurate,
        this is a real signal worth a human then editing the
        Destination directly (not auto-applied here -- a field report
        saying something's wrong shouldn't silently rewrite live
        content without a moderator's own judgment).
        """
        task = self.get_object()
        if not hasattr(task, "report"):
            return Response({"detail": "No report submitted yet."}, status=400)

        decision = request.data.get("decision")
        if decision not in (FieldVerificationReport.ReviewStatus.APPROVED, FieldVerificationReport.ReviewStatus.REJECTED):
            return Response({"detail": "decision must be 'approved' or 'rejected'."}, status=400)

        report = task.report
        report.review_status = decision
        report.reviewed_by = request.user
        report.review_note = request.data.get("note", "")
        report.save(update_fields=["review_status", "reviewed_by", "review_note"])

        task.status = FieldVerificationTask.Status.REVIEWED
        task.save(update_fields=["status"])

        return Response(FieldVerificationTaskSerializer(task).data)