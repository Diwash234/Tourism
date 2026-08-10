"""
safety/views.py

Polling-based, deliberately -- not WebSocket/Django Channels. A trusted
contact's page re-fetches GET /trips/shared/<token>/ every N seconds on
the frontend. Simpler to build and reason about correctly first; true
push-based real-time is a bigger, separate addition if genuinely needed
once this is working end-to-end.
"""
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import TrustedContact, SharedTrip, LocationPing, SOSAlert
from .serializers import (
    TrustedContactSerializer, SharedTripSerializer, LocationPingSerializer, SOSAlertSerializer,
)
from notifications.services import send_email_notification, send_sms_notification


class TrustedContactViewSet(viewsets.ModelViewSet):
    """Standard CRUD, scoped to the logged-in user's own contacts only."""
    serializer_class = TrustedContactSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return TrustedContact.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class SharedTripViewSet(viewsets.ModelViewSet):
    """
    Standard CRUD for the trip owner (create/end/view their own trips).
    The trusted contact's read-only view of an ACTIVE trip is a separate
    public endpoint below (SharedTripPublicView) -- they don't need or
    get an account, just the share_token.
    """
    serializer_class = SharedTripSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return SharedTrip.objects.filter(user=self.request.user).prefetch_related("trusted_contacts", "pings")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=["post"])
    def ping(self, request, pk=None):
        """
        POST /trips/{id}/ping/  {"latitude": ..., "longitude": ...}
        Records a new position during an active trip. Only the trip
        owner can post pings for their own trip.
        """
        trip = self.get_object()
        if not trip.is_valid():
            return Response({"detail": "This trip has ended or expired."}, status=status.HTTP_400_BAD_REQUEST)

        serializer = LocationPingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(trip=trip)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def end(self, request, pk=None):
        """POST /trips/{id}/end/ -- explicit revoke, doesn't wait for expires_at."""
        trip = self.get_object()
        trip.is_active = False
        trip.save(update_fields=["is_active"])
        return Response({"message": "Trip sharing ended."})


class SharedTripPublicView(APIView):
    """
    GET /trips/shared/<uuid:token>/
    What a TrustedContact actually polls -- no authentication, just the
    unguessable token. Returns 404 for an invalid/expired/ended trip
    rather than distinguishing "wrong token" from "expired trip", so a
    guessed token can't be used to probe which trips exist.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request, token):
        trip = get_object_or_404(SharedTrip, share_token=token)
        if not trip.is_valid():
            return Response({"detail": "This trip is no longer being shared."}, status=status.HTTP_404_NOT_FOUND)
        return Response(SharedTripSerializer(trip).data)


class SOSAlertViewSet(viewsets.ModelViewSet):
    """
    Create: any authenticated user, for themselves. Update (resolve/
    false-alarm status change): also self-service -- an SOS is personal,
    not something requiring an admin to close out, though emergency-role
    staff reading the emergency dashboard may see it too (not built
    here -- that's the emergency-response queue itself, a separate,
    bigger feature this doesn't try to replace).
    """
    serializer_class = SOSAlertSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return SOSAlert.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        alert = serializer.save(user=self.request.user)
        self._notify_trusted_contacts(alert)

    def _notify_trusted_contacts(self, alert):
        """
        Best-effort notification -- an SOS firing must never itself
        crash on a bad email/phone number. Ties into #2 (Twilio) from
        earlier this session for the SMS leg.
        """
        contacts = list(alert.user.trusted_contacts.all())
        alert.notified_contacts.set(contacts)

        location_note = (
            f"Last known location: {alert.latitude}, {alert.longitude}"
            if alert.latitude and alert.longitude else "Location not available."
        )
        message = f"{alert.user.first_name or alert.user.email} triggered an SOS alert. {location_note} {alert.message}".strip()

        for contact in contacts:
            if contact.email:
                try:
                    send_email_notification(contact.email, "SOS Alert", message)
                except Exception:
                    pass  # never let one bad contact block notifying the rest
            if contact.phone_number:
                try:
                    send_sms_notification(str(contact.phone_number), message)
                except Exception:
                    pass

    @action(detail=True, methods=["post"])
    def resolve(self, request, pk=None):
        """POST /sos/{id}/resolve/  {"status": "resolved" | "false_alarm"}"""
        alert = self.get_object()
        new_status = request.data.get("status", SOSAlert.Status.RESOLVED)
        if new_status not in (SOSAlert.Status.RESOLVED, SOSAlert.Status.FALSE_ALARM):
            return Response({"detail": "status must be 'resolved' or 'false_alarm'."}, status=status.HTTP_400_BAD_REQUEST)
        alert.status = new_status
        alert.resolved_at = timezone.now()
        alert.save(update_fields=["status", "resolved_at"])
        return Response(SOSAlertSerializer(alert).data)