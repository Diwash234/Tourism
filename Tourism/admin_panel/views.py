from django.shortcuts import render

# Create your views here.
from django.utils import timezone
from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from tourist.models import Hotel
from .models import HotelAssignment, AdminTask
from .permissions import IsSuperAdmin, IsSuperAdminOrAssignedAdmin
from .serializers import HotelAssignmentSerializer, AdminTaskSerializer


class HotelAssignmentViewSet(viewsets.ModelViewSet):
    """
    Only super admins can create/delete assignments (who manages which
    hotel). A staff admin can list/view their own assignments.
    """

    serializer_class = HotelAssignmentSerializer
    filterset_fields = ["hotel", "admin"]

    def get_permissions(self):
        if self.action in ("create", "destroy", "update", "partial_update"):
            return [IsSuperAdmin()]
        return [IsSuperAdminOrAssignedAdmin()]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return HotelAssignment.objects.none()
        if self.request.user.is_superuser:
            return HotelAssignment.objects.select_related("hotel", "admin")
        return HotelAssignment.objects.filter(admin=self.request.user).select_related("hotel", "admin")


class AdminTaskViewSet(viewsets.ModelViewSet):
    """
    Super admins create/assign tasks to any staff admin. Staff admins can
    only see and update the status of tasks assigned to them.
    """

    serializer_class = AdminTaskSerializer
    filterset_fields = ["status", "priority", "assigned_to", "related_hotel"]

    def get_permissions(self):
        if self.action in ("create", "destroy"):
            return [IsSuperAdmin()]
        return [IsSuperAdminOrAssignedAdmin()]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return AdminTask.objects.none()
        if self.request.user.is_superuser:
            return AdminTask.objects.select_related("assigned_to", "assigned_by", "related_hotel")
        return AdminTask.objects.filter(assigned_to=self.request.user).select_related(
            "assigned_to", "assigned_by", "related_hotel"
        )

    def perform_update(self, serializer):
        instance = serializer.save()
        if instance.status == AdminTask.Status.COMPLETED and instance.completed_at is None:
            instance.completed_at = timezone.now()
            instance.save(update_fields=["completed_at"])


class MyHotelsView(APIView):
    """GET /api/v1/admin-panel/my-hotels/ — hotels the logged-in staff admin manages."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from tourist.serializers import HotelSerializer

        if request.user.is_superuser:
            hotels = Hotel.objects.all()
        else:
            hotel_ids = HotelAssignment.objects.filter(admin=request.user).values_list("hotel_id", flat=True)
            hotels = Hotel.objects.filter(id__in=hotel_ids)
        return Response(HotelSerializer(hotels, many=True).data)


class AdminDashboardSummaryView(APIView):
    """
    GET /api/v1/admin-panel/dashboard-summary/ — quick counts for whoever's
    logged in: pending tasks, assigned hotel count, overdue tasks. Super
    admins see platform-wide totals instead.
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        if user.is_superuser:
            tasks = AdminTask.objects.all()
            hotel_count = Hotel.objects.count()
        else:
            tasks = AdminTask.objects.filter(assigned_to=user)
            hotel_count = HotelAssignment.objects.filter(admin=user).count()

        today = timezone.now().date()
        return Response({
            "assigned_hotel_count": hotel_count,
            "pending_tasks": tasks.filter(status=AdminTask.Status.PENDING).count(),
            "in_progress_tasks": tasks.filter(status=AdminTask.Status.IN_PROGRESS).count(),
            "completed_tasks": tasks.filter(status=AdminTask.Status.COMPLETED).count(),
            "overdue_tasks": tasks.filter(due_date__lt=today).exclude(status=AdminTask.Status.COMPLETED).count(),
            "is_super_admin": user.is_superuser,
        })