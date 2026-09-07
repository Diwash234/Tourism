from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q

from admin_panel.models import HotelAssignment
from .models import Booking, HotelReview
from .permissions import IsOwnerOrHotelAdminOrSuperAdmin, IsHotelReviewOwnerOrReadOnly
from .serializers import BookingSerializer, BookingStatusUpdateSerializer, HotelReviewSerializer


class BookingViewSet(viewsets.ModelViewSet):
    """
    A tourist creates/lists/cancels their own bookings. A staff admin
    assigned to that hotel (or a super admin) can see/manage bookings for
    hotels they're responsible for, via the `confirm`/`cancel` actions.
    """

    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrHotelAdminOrSuperAdmin]
    filterset_fields = ["hotel", "status"]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Booking.objects.none()
        user = self.request.user
        if user.is_superuser:
            return Booking.objects.select_related("hotel", "user")

        managed_hotel_ids = HotelAssignment.objects.filter(admin=user).values_list("hotel_id", flat=True)
        from django.db.models import Q

        return Booking.objects.filter(Q(user=user) | Q(hotel_id__in=managed_hotel_ids)).select_related("hotel", "user")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def perform_destroy(self, instance):
        if instance.status == Booking.Status.COMPLETED:
            from rest_framework.exceptions import ValidationError
            raise ValidationError("Completed bookings are retained and cannot be deleted")
        instance.status=Booking.Status.CANCELLED
        instance.save(update_fields=["status","updated_at"])

    @action(detail=True, methods=["post"])
    def confirm(self, request, pk=None):
        booking = self.get_object()
        self._require_hotel_manager(request, booking)
        booking.status = Booking.Status.CONFIRMED
        booking.save(update_fields=["status"])
        return Response(BookingSerializer(booking).data)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        booking = self.get_object()
        # A tourist can cancel their own booking; a hotel manager/super
        # admin can cancel any booking for their hotel.
        if booking.user != request.user:
            self._require_hotel_manager(request, booking)
        booking.status = Booking.Status.CANCELLED
        booking.save(update_fields=["status"])
        return Response(BookingSerializer(booking).data)

    @action(detail=True, methods=["post"])
    def complete(self, request, pk=None):
        booking = self.get_object()
        self._require_hotel_manager(request, booking)
        booking.status = Booking.Status.COMPLETED
        booking.save(update_fields=["status"])
        return Response(BookingSerializer(booking).data)

    def _require_hotel_manager(self, request, booking):
        if request.user.is_superuser:
            return
        if not HotelAssignment.objects.filter(hotel=booking.hotel, admin=request.user).exists():
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied("You don't manage this hotel.")


class HotelReviewViewSet(viewsets.ModelViewSet):
    queryset = HotelReview.objects.select_related("hotel", "user")
    serializer_class = HotelReviewSerializer
    permission_classes = [IsHotelReviewOwnerOrReadOnly]
    filterset_fields = ["hotel", "user"]

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.is_authenticated:
            return queryset.filter(Q(moderation_status="approved") | Q(user=self.request.user)).exclude(moderation_status="archived")
        return queryset.filter(moderation_status="approved")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user, moderation_status="pending")

    def perform_update(self, serializer):
        serializer.save(moderation_status="pending", moderation_note="", moderated_by=None, moderated_at=None)

    def perform_destroy(self, instance):
        from django.utils import timezone
        instance.moderation_status = "archived"
        instance.moderation_note = "Withdrawn by review owner"
        instance.moderated_at = timezone.now()
        instance.save(update_fields=["moderation_status", "moderation_note", "moderated_at"])