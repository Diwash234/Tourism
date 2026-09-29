"""
Webhook System.

Provides a webhook dispatcher that:
- Registers webhook endpoints
- Sends webhooks with retry logic
- Logs all webhook deliveries
- Supports events: booking.created, booking.cancelled, review.created, user.registered

Usage:
    from tourist.webhooks import WebhookDispatcher
    dispatcher = WebhookDispatcher()
    dispatcher.dispatch("booking.created", {"booking_id": 1, ...})
"""

import hashlib
import hmac
import json
import logging
import time
import uuid
from datetime import timedelta

import requests
from django.conf import settings
from django.core.cache import cache
from django.db import models
from django.utils import timezone

logger = logging.getLogger(__name__)

# Supported webhook events
WEBHOOK_EVENTS = {
    "booking.created": "A new booking has been created",
    "booking.cancelled": "A booking has been cancelled",
    "booking.confirmed": "A booking has been confirmed",
    "review.created": "A new review has been submitted",
    "review.updated": "A review has been updated",
    "user.registered": "A new user has registered",
    "user.updated": "A user profile has been updated",
    "destination.created": "A new destination has been added",
    "destination.updated": "A destination has been updated",
}

# Retry configuration
MAX_RETRIES = 3
RETRY_DELAYS = [1, 5, 15]  # seconds between retries
WEBHOOK_TIMEOUT = 10  # seconds
WEBHOOK_CACHE_PREFIX = "webhook"


class WebhookEndpoint(models.Model):
    """A registered webhook endpoint."""

    class EventType(models.TextChoices):
        BOOKING_CREATED = "booking.created", "Booking Created"
        BOOKING_CANCELLED = "booking.cancelled", "Booking Cancelled"
        BOOKING_CONFIRMED = "booking.confirmed", "Booking Confirmed"
        REVIEW_CREATED = "review.created", "Review Created"
        REVIEW_UPDATED = "review.updated", "Review Updated"
        USER_REGISTERED = "user.registered", "User Registered"
        USER_UPDATED = "user.updated", "User Updated"
        DESTINATION_CREATED = "destination.created", "Destination Created"
        DESTINATION_UPDATED = "destination.updated", "Destination Updated"

    name = models.CharField(max_length=200)
    url = models.URLField(max_length=500)
    secret = models.CharField(max_length=200, blank=True, help_text="Secret for HMAC signature verification")
    event_types = models.JSONField(default=list, help_text="List of event types to subscribe to")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} ({self.url})"


class WebhookDelivery(models.Model):
    """Log of a webhook delivery attempt."""

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        SUCCESS = "success", "Success"
        FAILED = "failed", "Failed"
        RETRYING = "retrying", "Retrying"

    webhook = models.ForeignKey(WebhookEndpoint, on_delete=models.CASCADE, related_name="deliveries")
    event_type = models.CharField(max_length=50)
    payload = models.JSONField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    response_status = models.PositiveIntegerField(null=True, blank=True)
    response_body = models.TextField(blank=True)
    error_message = models.TextField(blank=True)
    attempt_count = models.PositiveSmallIntegerField(default=0)
    max_attempts = models.PositiveSmallIntegerField(default=MAX_RETRIES)
    next_retry_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "next_retry_at"]),
            models.Index(fields=["event_type", "created_at"]),
        ]

    def __str__(self):
        return f"{self.event_type} → {self.webhook.name} ({self.status})"


class WebhookDispatcher:
    """
    Dispatches webhook events to registered endpoints.

    Usage:
        dispatcher = WebhookDispatcher()
        dispatcher.dispatch("booking.created", {"booking_id": 1})
    """

    def __init__(self):
        self.endpoints = self._load_endpoints()

    def _load_endpoints(self):
        """Load active webhook endpoints from the database."""
        try:
            return list(WebhookEndpoint.objects.filter(is_active=True))
        except Exception:
            # Table might not exist yet (migrations not run)
            return []

    def register_endpoint(self, name, url, event_types, secret=""):
        """
        Register a new webhook endpoint.

        Args:
            name: Human-readable name for the endpoint.
            url: The URL to send webhooks to.
            event_types: List of event type strings to subscribe to.
            secret: Optional secret for HMAC signature.

        Returns:
            The created WebhookEndpoint instance.
        """
        endpoint = WebhookEndpoint.objects.create(
            name=name,
            url=url,
            secret=secret,
            event_types=event_types,
        )
        # Reload endpoints
        self.endpoints = self._load_endpoints()
        return endpoint

    def unregister_endpoint(self, endpoint_id):
        """Deactivate a webhook endpoint."""
        WebhookEndpoint.objects.filter(id=endpoint_id).update(is_active=False)
        self.endpoints = self._load_endpoints()

    def dispatch(self, event_type, payload):
        """
        Dispatch a webhook event to all registered endpoints.

        Args:
            event_type: The event type string (e.g. "booking.created").
            payload: The event data dict.

        Returns:
            List of WebhookDelivery instances created.
        """
        if event_type not in WEBHOOK_EVENTS:
            logger.warning(f"Unknown webhook event type: {event_type}")
            return []

        deliveries = []
        for endpoint in self.endpoints:
            if event_type not in endpoint.event_types:
                continue

            delivery = WebhookDelivery.objects.create(
                webhook=endpoint,
                event_type=event_type,
                payload=payload,
                status=WebhookDelivery.Status.PENDING,
            )
            deliveries.append(delivery)

            # Send immediately (could be queued for background processing)
            self._send_webhook(delivery)

        return deliveries

    def _send_webhook(self, delivery):
        """
        Send a webhook delivery with retry logic.
        """
        endpoint = delivery.webhook
        payload = delivery.payload

        # Build the webhook body
        webhook_body = {
            "id": str(uuid.uuid4()),
            "event": delivery.event_type,
            "created_at": timezone.now().isoformat(),
            "data": payload,
        }

        headers = {
            "Content-Type": "application/json",
            "User-Agent": "NepalTourism-Webhook/1.0",
            "X-Webhook-Event": delivery.event_type,
            "X-Webhook-ID": str(delivery.id),
        }

        # Add HMAC signature if secret is configured
        if endpoint.secret:
            signature = self._sign_payload(webhook_body, endpoint.secret)
            headers["X-Webhook-Signature"] = signature

        # Attempt delivery with retries
        for attempt in range(1, delivery.max_attempts + 1):
            delivery.attempt_count = attempt
            delivery.save(update_fields=["attempt_count"])

            try:
                response = requests.post(
                    endpoint.url,
                    json=webhook_body,
                    headers=headers,
                    timeout=WEBHOOK_TIMEOUT,
                )

                delivery.response_status = response.status_code
                delivery.response_body = response.text[:1000]  # Truncate long responses

                if response.status_code >= 200 and response.status_code < 300:
                    delivery.status = WebhookDelivery.Status.SUCCESS
                    delivery.delivered_at = timezone.now()
                    delivery.save()
                    logger.info(f"Webhook {delivery.id} delivered successfully to {endpoint.url}")
                    return True

                # Non-2xx response
                delivery.error_message = f"HTTP {response.status_code}: {response.text[:200]}"

                if attempt < delivery.max_attempts:
                    delivery.status = WebhookDelivery.Status.RETRYING
                    delay = RETRY_DELAYS[min(attempt - 1, len(RETRY_DELAYS) - 1)]
                    delivery.next_retry_at = timezone.now() + timedelta(seconds=delay)
                    delivery.save()
                    time.sleep(delay)
                else:
                    delivery.status = WebhookDelivery.Status.FAILED
                    delivery.save()
                    logger.error(f"Webhook {delivery.id} failed after {attempt} attempts: {delivery.error_message}")
                    return False

            except requests.RequestException as e:
                delivery.error_message = str(e)[:500]

                if attempt < delivery.max_attempts:
                    delivery.status = WebhookDelivery.Status.RETRYING
                    delay = RETRY_DELAYS[min(attempt - 1, len(RETRY_DELAYS) - 1)]
                    delivery.next_retry_at = timezone.now() + timedelta(seconds=delay)
                    delivery.save()
                    time.sleep(delay)
                else:
                    delivery.status = WebhookDelivery.Status.FAILED
                    delivery.save()
                    logger.error(f"Webhook {delivery.id} failed after {attempt} attempts: {e}")
                    return False

        return False

    def _sign_payload(self, payload, secret):
        """Generate HMAC-SHA256 signature for webhook payload."""
        body = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        signature = hmac.new(
            secret.encode("utf-8"),
            body.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        return f"sha256={signature}"

    def retry_failed(self, max_age_hours=24):
        """
        Retry failed webhook deliveries within the last N hours.

        Returns:
            Number of webhooks retried.
        """
        cutoff = timezone.now() - timedelta(hours=max_age_hours)
        failed = WebhookDelivery.objects.filter(
            status=WebhookDelivery.Status.FAILED,
            attempt_count__lt=models.F("max_attempts"),
            created_at__gte=cutoff,
        )

        retried = 0
        for delivery in failed:
            delivery.status = WebhookDelivery.Status.PENDING
            delivery.save()
            self._send_webhook(delivery)
            retried += 1

        return retried

    def get_delivery_stats(self, hours=24):
        """
        Get webhook delivery statistics for the last N hours.
        """
        cutoff = timezone.now() - timedelta(hours=hours)

        stats = WebhookDelivery.objects.filter(
            created_at__gte=cutoff,
        ).values("status").annotate(count=models.Count("id"))

        result = {s["status"]: s["count"] for s in stats}
        result["total"] = sum(result.values())
        result["period_hours"] = hours
        return result


# Singleton instance for convenience
_default_dispatcher = None


def get_dispatcher():
    """Get or create the default webhook dispatcher."""
    global _default_dispatcher
    if _default_dispatcher is None:
        _default_dispatcher = WebhookDispatcher()
    return _default_dispatcher


def dispatch_event(event_type, payload):
    """
    Convenience function to dispatch a webhook event.

    Usage:
        from tourist.webhooks import dispatch_event
        dispatch_event("booking.created", {"booking_id": 1})
    """
    dispatcher = get_dispatcher()
    return dispatcher.dispatch(event_type, payload)
