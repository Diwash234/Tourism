"""Self-service privacy actions: account deletion and newsletter unsubscribe.

Account deletion reuses the admin anonymisation routine (retention.py) so
there is one audited way to remove a person, then deletes records that only
exist for that person (documents, trusted contacts, trip plans, chats...).
Bookings, safety alerts and security logs are kept, detached from the
person's identity, because they are operational/safety records; the privacy
policy says so.
"""
import csv
import logging

from django.conf import settings
from django.core import signing
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.http import HttpResponse
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import NewsletterSignup

logger = logging.getLogger(__name__)

UNSUBSCRIBE_SALT = "newsletter-unsubscribe"


def unsubscribe_token(email: str) -> str:
    return signing.dumps(str(email).strip().lower(), salt=UNSUBSCRIBE_SALT)


def unsubscribe_url(email: str) -> str:
    base = (getattr(settings, "FRONTEND_URL", "") or "").rstrip("/")
    return f"{base}/unsubscribe?token={unsubscribe_token(email)}"


class AccountDeletionView(APIView):
    """POST /api/v1/auth/account/delete/ - delete the signed-in account.

    Body: ``{"password": "..."}`` for password accounts, or
    ``{"confirm_email": "<your email>"}`` for Google/GitHub sign-in accounts.
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = request.user
        if user.is_superuser:
            return Response({"detail": "Super administrator accounts cannot be deleted here. Ask another administrator to transfer ownership first."},
                            status=status.HTTP_403_FORBIDDEN)
        if user.has_usable_password():
            if not user.check_password(str(request.data.get("password") or "")):
                return Response({"detail": "The password is incorrect.", "field": "password"}, status=status.HTTP_400_BAD_REQUEST)
        elif str(request.data.get("confirm_email") or "").strip().lower() != user.email.lower():
            return Response({"detail": "Type the email address of this account to confirm.", "field": "confirm_email"},
                            status=status.HTTP_400_BAD_REQUEST)

        from .retention import anonymize_user
        email = user.email
        removed = {}
        with transaction.atomic():
            for name, qs in (
                ("travel_documents", user.traveler_documents.all()),
                ("trusted_contacts", user.trusted_contacts.all()),
                ("trip_plans", user.travel_plans.all()),
                ("saved_routes", user.routes.all()),
                ("chat_conversations", user.chat_conversations.all()),
                ("newsletter", NewsletterSignup.objects.filter(email__iexact=email)),
            ):
                removed[name] = qs.count()
                qs.delete()
            # Live location shares: end them and drop the recorded pings.
            from .models import LocationPing
            removed["location_pings"] = LocationPing.objects.filter(trip__user=user).count()
            LocationPing.objects.filter(trip__user=user).delete()
            user.shared_trips.update(is_active=False)
            from django.apps import apps
            budgets = apps.get_model("tourist", "Budget").objects.filter(user=user)
            removed["budgets"] = budgets.count()
            budgets.delete()
            # Records other people rely on (a provider's booking, a guide's
            # request log, a reviewed application) stay, minus who you are.
            removed["booking_contact_details"] = apps.get_model("tourist", "MarketplaceOrder").objects.filter(user=user).update(
                guest_name="Deleted User", guest_email="", guest_phone="", notes="")
            apps.get_model("tourist", "GuideBookingRequest").objects.filter(tourist=user).update(message="")
            apps.get_model("tourist", "GuideApplication").objects.filter(user=user).update(full_name="Deleted User", phone="")
            for one_to_one in ("preference_profile", "notification_preferences"):
                try:
                    getattr(user, one_to_one).delete()
                    removed[one_to_one] = 1
                except ObjectDoesNotExist:  # nothing stored for this user
                    removed[one_to_one] = 0
            anonymize_user(user, actor=user)
        logger.info("Self-service account deletion for user #%s", user.pk)
        return Response({
            "deleted": True,
            "removed": removed,
            "kept": ("Booking records and safety (SOS) alerts are kept without your name or contact details, for the "
                     "providers involved and for safety follow-up. Security logs, which can include your email and IP "
                     "address, are kept for their retention period to protect the service. Reviews you published stay, "
                     "shown as 'Deleted User'."),
        })


class NewsletterUnsubscribeView(APIView):
    """POST /api/v1/newsletter/unsubscribe/ with ``{"token"}`` (from an email
    link) or ``{"email"}`` (typed). The reply is the same whether or not the
    address was subscribed, so the form cannot be used to test addresses."""

    permission_classes = [permissions.AllowAny]
    throttle_scope = "newsletter"

    def post(self, request):
        token = str(request.data.get("token") or "").strip()
        if token:
            try:
                email = signing.loads(token, salt=UNSUBSCRIBE_SALT)
            except signing.BadSignature:
                return Response({"detail": "This unsubscribe link is not valid. Enter your email address instead."},
                                status=status.HTTP_400_BAD_REQUEST)
        else:
            email = str(request.data.get("email") or "").strip().lower()
            if "@" not in email or len(email) > 254:
                return Response({"detail": "Enter the email address you subscribed with."}, status=status.HTTP_400_BAD_REQUEST)
        NewsletterSignup.objects.filter(email__iexact=email).update(is_active=False)
        return Response({"message": "Done. If that address was subscribed, it will not receive travel-note emails any more."})


class NewsletterExportView(APIView):
    """GET /api/v1/admin/newsletter/export.csv - active subscribers with their
    personal unsubscribe link, for the footer of any mailing."""

    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="newsletter-subscribers.csv"'
        writer = csv.writer(response)
        writer.writerow(["email", "subscribed_at", "unsubscribe_url"])
        for row in NewsletterSignup.objects.filter(is_active=True).order_by("created_at"):
            writer.writerow([row.email, row.created_at.isoformat(), unsubscribe_url(row.email)])
        return response
