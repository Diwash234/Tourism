"""
New file: Tourism/tourist/views_family_safety.py

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

from django.db.models import Q
from rest_framework import serializers

from .models import TrustedContact, SharedTrip, LocationPing, SOSAlert
from .serializers_family_safety import (
    TrustedContactSerializer, SharedTripSerializer, LocationPingSerializer, SOSAlertSerializer,
)
from .utils import send_email_notification, send_sms_notification


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
        trip = serializer.save(user=self.request.user)
        notify_family_members(
            self.request.user,
            "Live location sharing started",
            f"{self.request.user.first_name or self.request.user.email} started sharing their live location ({trip.label or 'trip'}).",
        )

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
        notify_family_members(alert.user, "🚨 SOS ALERT", message)

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

# ---------------------------------------------------------------------------
# Family linking (account <-> account)
# ---------------------------------------------------------------------------
from django.contrib.auth import get_user_model  # noqa: E402
from rest_framework.decorators import action as drf_action  # noqa: E402

from .models import FamilyLink, Notification  # noqa: E402
from .serializers_family_safety import (  # noqa: E402
    FamilyLinkSerializer, FamilyMemberSerializer,
)


def _notify(user, title, message):
    """Best-effort in-app notification row."""
    try:
        Notification.objects.create(user=user, title=title, message=message)
    except Exception:
        pass


def notify_family_members(owner, title, message, exclude=None):
    """Notify every ACCEPTED family member of `owner` (in-app)."""
    ids = FamilyLink.objects.filter(
        status=FamilyLink.Status.ACCEPTED, requester=owner
    ).values_list("member_id", flat=True)
    ids2 = FamilyLink.objects.filter(
        status=FamilyLink.Status.ACCEPTED, member=owner
    ).values_list("requester_id", flat=True)
    for uid in set(list(ids) + list(ids2)):
        if exclude and uid == exclude.id:
            continue
        try:
            UserM = get_user_model()
            _notify(UserM.objects.get(id=uid), title, message)
        except Exception:
            pass


class FamilyLinkViewSet(viewsets.ModelViewSet):
    """Manage family links. A link is created by one user and accepted by
    the other; once accepted, both sides can see each other's live
    location / trip history and receive SOS + trip notifications."""

    serializer_class = FamilyLinkSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return FamilyLink.objects.filter(
            Q(requester=self.request.user) | Q(member=self.request.user)
        )

    def perform_create(self, serializer):
        username_or_email = serializer.validated_data.pop("username_or_email", "")
        if not username_or_email:
            raise serializers.ValidationError("Provide the family member's username or email.")
        UserM = get_user_model()
        member = (
            UserM.objects.filter(email__iexact=username_or_email).first()
            or UserM.objects.filter(username__iexact=username_or_email).first()
            if hasattr(UserM, "username")
            else UserM.objects.filter(email__iexact=username_or_email).first()
        )
        if member is None:
            raise serializers.ValidationError("No account found with that username/email.")
        if member.id == self.request.user.id:
            raise serializers.ValidationError("You can't link yourself.")
        link, created = FamilyLink.objects.get_or_create(
            requester=self.request.user, member=member,
            defaults={"relationship": serializer.validated_data.get("relationship", "")},
        )
        if not created:
            if link.status == FamilyLink.Status.DECLINED:
                link.status = FamilyLink.Status.PENDING
                link.save(update_fields=["status"])
            raise serializers.ValidationError("A family link with this person already exists.")
        _notify(
            member,
            "Family link request",
            f"{self.request.user.first_name or self.request.user.email} wants to link as family. Accept it in the Family Safety page.",
        )
        # give DRF the created instance so serializer.data serializes it
        serializer.instance = link

    @drf_action(detail=True, methods=["post"])
    def accept(self, request, pk=None):
        link = self.get_object()
        if link.member_id != request.user.id:
            return Response({"detail": "Only the invited member can accept."}, status=status.HTTP_403_FORBIDDEN)
        if link.status != FamilyLink.Status.PENDING:
            return Response({"detail": "This link is not pending."}, status=status.HTTP_400_BAD_REQUEST)
        link.status = FamilyLink.Status.ACCEPTED
        link.accepted_at = timezone.now()
        link.save(update_fields=["status", "accepted_at"])
        _notify(
            link.requester,
            "Family link accepted",
            f"{request.user.first_name or request.user.email} accepted your family link.",
        )
        return Response(FamilyLinkSerializer(link, context={"request": request}).data)

    @drf_action(detail=True, methods=["post"])
    def decline(self, request, pk=None):
        link = self.get_object()
        if link.member_id != request.user.id:
            return Response({"detail": "Only the invited member can decline."}, status=status.HTTP_403_FORBIDDEN)
        link.status = FamilyLink.Status.DECLINED
        link.save(update_fields=["status"])
        return Response({"message": "Family link declined."})

    def perform_destroy(self, instance):
        # either side can unlink
        instance.delete()


class FamilyMembersView(APIView):
    """GET /safety/family/members/  -- live status of every accepted
    family member: active trip + latest ping (live location), recent trip
    history and any ACTIVE SOS alerts."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        links = FamilyLink.objects.filter(
            status=FamilyLink.Status.ACCEPTED
        ).filter(Q(requester=user) | Q(member=user))

        members = []
        for link in links.select_related("requester", "member"):
            other = link.member if link.requester_id == user.id else link.requester
            trips = SharedTrip.objects.filter(user=other).prefetch_related("pings", "sos_alerts")[:5]
            history = []
            live_trip = None
            latest_ping = None
            for trip in trips:
                item = {
                    "id": trip.id,
                    "label": trip.label or "Trip",
                    "started_at": trip.started_at.isoformat(),
                    "is_valid": trip.is_valid(),
                }
                ping = trip.pings.first()
                if ping:
                    item["latest_ping"] = {
                        "latitude": str(ping.latitude),
                        "longitude": str(ping.longitude),
                        "recorded_at": ping.recorded_at.isoformat(),
                    }
                if trip.is_valid() and live_trip is None:
                    live_trip = item
                    latest_ping = item.get("latest_ping")
                history.append(item)
            active_sos = [
                {
                    "id": a.id,
                    "message": a.message,
                    "latitude": str(a.latitude) if a.latitude else None,
                    "longitude": str(a.longitude) if a.longitude else None,
                    "triggered_at": a.triggered_at.isoformat(),
                }
                for a in SOSAlert.objects.filter(user=other, status=SOSAlert.Status.ACTIVE)[:3]
            ]
            members.append({
                "link_id": link.id,
                "user_id": other.id,
                "name": (other.first_name or other.full_name or other.email or "").strip() or other.email,
                "username": getattr(other, "username", "") or other.email,
                "relationship": link.relationship,
                "is_live": live_trip is not None,
                "live_trip": live_trip,
                "latest_ping": latest_ping,
                "history": history[:5],
                "active_sos": active_sos,
            })
        return Response(FamilyMemberSerializer(members, many=True).data)
