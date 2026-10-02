"""
Webhook system for external integrations.
"""
import hashlib
import hmac
import json
import logging
import time
from typing import Any, Callable, Optional

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class WebhookManager:
    """
    Manages webhook subscriptions and deliveries.

    Usage:
        webhook = WebhookManager()
        webhook.register("booking.created", handler_function)
        webhook.trigger("booking.created", {"booking_id": 123})
    """

    def __init__(self):
        self._handlers = {}
        self._subscriptions = []

    def register(self, event: str, handler: Callable):
        """Register a handler for an event."""
        if event not in self._handlers:
            self._handlers[event] = []
        self._handlers[event].append(handler)

    def subscribe(self, url: str, events: list, secret: str = ""):
        """Subscribe an external URL to events."""
        self._subscriptions.append({
            "url": url,
            "events": events,
            "secret": secret,
        })

    def trigger(self, event: str, data: dict):
        """Trigger an event and notify all subscribers."""
        # Call local handlers
        for handler in self._handlers.get(event, []):
            try:
                handler(data)
            except Exception as exc:
                logger.error("Webhook handler error for %s: %s", event, exc)

        # Notify external subscribers
        for sub in self._subscriptions:
            if event in sub["events"]:
                self._deliver(sub["url"], event, data, sub["secret"])

    def _deliver(self, url: str, event: str, data: dict, secret: str):
        """Deliver a webhook to an external URL."""
        payload = json.dumps({
            "event": event,
            "timestamp": time.time(),
            "data": data,
        })

        headers = {
            "Content-Type": "application/json",
            "X-Webhook-Event": event,
            "X-Webhook-Timestamp": str(int(time.time())),
        }

        # Sign the payload if a secret is provided
        if secret:
            signature = hmac.new(
                secret.encode(),
                payload.encode(),
                hashlib.sha256,
            ).hexdigest()
            headers["X-Webhook-Signature"] = f"sha256={signature}"

        try:
            response = requests.post(
                url,
                data=payload,
                headers=headers,
                timeout=10,
            )
            response.raise_for_status()
            logger.info("Webhook delivered to %s: %s", url, event)
        except requests.RequestException as exc:
            logger.error("Webhook delivery failed to %s: %s", url, exc)


# Global webhook instance
webhooks = WebhookManager()
