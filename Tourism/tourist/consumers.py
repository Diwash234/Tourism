"""
WebSocket consumers for real-time features.

Three consumers are provided:
- NotificationConsumer: pushes real-time notifications to connected users
- LocationSharingConsumer: real-time location sharing for trip collaboration
- SOSAlertConsumer: emergency alert broadcast to nearby users

All consumers use Django Channels' channel layer for group-based broadcasting.
Authentication is handled via JWT token in the query string (since browsers
cannot set custom headers on WebSocket connections).
"""

import json
import logging

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.conf import settings
from django.db.models import Q

logger = logging.getLogger(__name__)


@database_sync_to_async
def get_user_from_token(token):
    """Validate a JWT token and return the associated user."""
    try:
        from rest_framework_simplejwt.tokens import AccessToken
        from django.contrib.auth import get_user_model

        AccessToken(token)  # raises if invalid/expired
        user_id = AccessToken(token)["user_id"]
        User = get_user_model()
        return User.objects.get(id=user_id, is_active=True)
    except Exception:
        return None


@database_sync_to_async
def get_user_groups(user):
    """Return the channel-layer group names a user belongs to."""
    return [f"user_{user.id}", "broadcast"]


@database_sync_to_async
def get_nearby_users(latitude, longitude, radius_km=10):
    """Find active users within a radius (for SOS broadcast)."""
    from django.contrib.auth import get_user_model
    from .utils import haversine_distance

    User = get_user_model()
    users = User.objects.filter(
        is_active=True,
        latitude__isnull=False,
        longitude__isnull=False,
    ).exclude(latitude=0, longitude=0)

    nearby = []
    for user in users:
        dist = haversine_distance(latitude, longitude, float(user.latitude), float(user.longitude))
        if dist <= radius_km:
            nearby.append(user.id)
    return nearby


class NotificationConsumer(AsyncJsonWebsocketConsumer):
    """
    Pushes real-time notifications to connected users.

    Clients connect to: ws://host/ws/notifications/?token=<jwt>
    On connect, the user is added to their personal notification group.
    Notifications are pushed as JSON: {"type": "notification", "payload": {...}}
    """

    async def connect(self):
        self.user = None
        self.group_names = []

        # Extract token from query string
        query_string = self.scope.get("query_string", b"").decode("utf-8")
        params = {}
        for pair in query_string.split("&"):
            if "=" in pair:
                key, value = pair.split("=", 1)
                params[key] = value

        token = params.get("token", "")
        if token:
            self.user = await get_user_from_token(token)

        if not self.user:
            await self.close(code=4001)
            return

        self.group_names = await get_user_groups(self.user)

        for group_name in self.group_names:
            await self.channel_layer.group_add(group_name, self.channel_name)

        await self.accept()
        await self.send_json({
            "type": "notification.connected",
            "user_id": self.user.id,
            "message": "Connected to notification stream",
        })

    async def disconnect(self, code):
        for group_name in getattr(self, "group_names", []):
            await self.channel_layer.group_discard(group_name, self.channel_name)

    async def receive_json(self, content, **kwargs):
        """Handle incoming messages from the client."""
        msg_type = content.get("type", "")

        if msg_type == "ping":
            await self.send_json({"type": "pong"})
        elif msg_type == "mark_read":
            notification_id = content.get("notification_id")
            if notification_id:
                await self._mark_notification_read(notification_id)
                await self.send_json({
                    "type": "notification.marked_read",
                    "notification_id": notification_id,
                })
        elif msg_type == "mark_all_read":
            count = await self._mark_all_notifications_read()
            await self.send_json({
                "type": "notification.all_marked_read",
                "count": count,
            })

    async def notification_message(self, event):
        """Handler for notification events sent via channel_layer.group_send."""
        await self.send_json({
            "type": "notification",
            "payload": event["payload"],
        })

    async def broadcast_message(self, event):
        """Handler for broadcast events sent to the 'broadcast' group."""
        await self.send_json({
            "type": "broadcast",
            "payload": event["payload"],
        })

    @database_sync_to_async
    def _mark_notification_read(self, notification_id):
        from .models import Notification
        Notification.objects.filter(
            id=notification_id,
            user=self.user,
            is_read=False,
        ).update(is_read=True)

    @database_sync_to_async
    def _mark_all_notifications_read(self):
        from .models import Notification
        return Notification.objects.filter(
            user=self.user,
            is_read=False,
        ).update(is_read=True)


class LocationSharingConsumer(AsyncJsonWebsocketConsumer):
    """
    Real-time location sharing for trip collaboration.

    Clients connect to: ws://host/ws/location/<trip_id>/?token=<jwt>
    Location updates are broadcast to all members of the trip group.
    """

    async def connect(self):
        self.user = None
        self.trip_id = self.scope["url_route"]["kwargs"]["trip_id"]
        self.group_name = f"location_trip_{self.trip_id}"

        # Extract token from query string
        query_string = self.scope.get("query_string", b"").decode("utf-8")
        params = {}
        for pair in query_string.split("&"):
            if "=" in pair:
                key, value = pair.split("=", 1)
                params[key] = value

        token = params.get("token", "")
        if token:
            self.user = await get_user_from_token(token)

        if not self.user:
            await self.close(code=4001)
            return

        # Verify user is a member of this trip
        is_member = await self._is_trip_member(self.user, self.trip_id)
        if not is_member:
            await self.close(code=4003)
            return

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        await self.send_json({
            "type": "location.connected",
            "trip_id": self.trip_id,
            "user_id": self.user.id,
        })

    async def disconnect(self, code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive_json(self, content, **kwargs):
        """Handle location updates from clients."""
        msg_type = content.get("type", "")

        if msg_type == "ping":
            await self.send_json({"type": "pong"})

        elif msg_type == "location.update":
            latitude = content.get("latitude")
            longitude = content.get("longitude")
            accuracy = content.get("accuracy")

            if latitude is None or longitude is None:
                await self.send_json({
                    "type": "error",
                    "message": "latitude and longitude are required",
                })
                return

            # Store the ping in the database
            await self._store_location_ping(latitude, longitude, accuracy)

            # Broadcast to trip members
            await self.channel_layer.group_send(
                self.group_name,
                {
                    "type": "location.update",
                    "payload": {
                        "user_id": self.user.id,
                        "latitude": latitude,
                        "longitude": longitude,
                        "accuracy": accuracy,
                        "timestamp": str(await self._get_timestamp()),
                    },
                },
            )

        elif msg_type == "location.request":
            # Request current locations of all trip members
            locations = await self._get_trip_locations()
            await self.send_json({
                "type": "location.snapshot",
                "trip_id": self.trip_id,
                "locations": locations,
            })

    async def location_update(self, event):
        """Handler for location update events."""
        await self.send_json({
            "type": "location.update",
            "payload": event["payload"],
        })

    @database_sync_to_async
    def _is_trip_member(self, user, trip_id):
        from .models import SharedTrip
        try:
            trip = SharedTrip.objects.get(id=trip_id)
            if trip.user == user:
                return True
            return trip.trusted_contacts.filter(
                Q(email=user.email) | Q(phone_number=user.phone_number)
            ).exists()
        except SharedTrip.DoesNotExist:
            return False

    @database_sync_to_async
    def _store_location_ping(self, latitude, longitude, accuracy):
        from .models import LocationPing, SharedTrip
        try:
            trip = SharedTrip.objects.get(id=self.trip_id)
            LocationPing.objects.create(
                trip=trip,
                latitude=latitude,
                longitude=longitude,
            )
        except SharedTrip.DoesNotExist:
            pass

    @database_sync_to_async
    def _get_trip_locations(self):
        from .models import LocationPing, SharedTrip
        try:
            trip = SharedTrip.objects.get(id=self.trip_id)
            pings = LocationPing.objects.filter(trip=trip).order_by("-recorded_at")[:20]
            return [
                {
                    "latitude": str(ping.latitude),
                    "longitude": str(ping.longitude),
                    "recorded_at": str(ping.recorded_at),
                }
                for ping in pings
            ]
        except SharedTrip.DoesNotExist:
            return []

    @database_sync_to_async
    def _get_timestamp(self):
        from django.utils import timezone
        return timezone.now()


class SOSAlertConsumer(AsyncJsonWebsocketConsumer):
    """
    Emergency alert broadcast to nearby users.

    Clients connect to: ws://host/ws/sos/?token=<jwt>
    SOS alerts are broadcast to all connected users within a configurable
    radius of the alert location.
    """

    async def connect(self):
        self.user = None
        self.group_name = "sos_alerts"

        # Extract token from query string
        query_string = self.scope.get("query_string", b"").decode("utf-8")
        params = {}
        for pair in query_string.split("&"):
            if "=" in pair:
                key, value = pair.split("=", 1)
                params[key] = value

        token = params.get("token", "")
        if token:
            self.user = await get_user_from_token(token)

        if not self.user:
            await self.close(code=4001)
            return

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        await self.send_json({
            "type": "sos.connected",
            "user_id": self.user.id,
            "message": "Connected to SOS alert stream",
        })

    async def disconnect(self, code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive_json(self, content, **kwargs):
        """Handle SOS alerts from clients."""
        msg_type = content.get("type", "")

        if msg_type == "ping":
            await self.send_json({"type": "pong"})

        elif msg_type == "sos.trigger":
            latitude = content.get("latitude")
            longitude = content.get("longitude")
            message = content.get("message", "")
            radius_km = content.get("radius_km", 10)

            if latitude is None or longitude is None:
                await self.send_json({
                    "type": "error",
                    "message": "latitude and longitude are required for SOS",
                })
                return

            # Store the SOS alert
            sos_id = await self._create_sos_alert(latitude, longitude, message)

            # Broadcast to all connected SOS users
            await self.channel_layer.group_send(
                self.group_name,
                {
                    "type": "sos.alert",
                    "payload": {
                        "sos_id": sos_id,
                        "user_id": self.user.id,
                        "latitude": latitude,
                        "longitude": longitude,
                        "message": message,
                        "radius_km": radius_km,
                        "timestamp": str(await self._get_timestamp()),
                    },
                },
            )

        elif msg_type == "sos.resolve":
            sos_id = content.get("sos_id")
            if sos_id:
                await self._resolve_sos_alert(sos_id)
                await self.channel_layer.group_send(
                    self.group_name,
                    {
                        "type": "sos.resolved",
                        "payload": {
                            "sos_id": sos_id,
                            "resolved_by": self.user.id,
                            "timestamp": str(await self._get_timestamp()),
                        },
                    },
                )

    async def sos_alert(self, event):
        """Handler for SOS alert events."""
        await self.send_json({
            "type": "sos.alert",
            "payload": event["payload"],
        })

    async def sos_resolved(self, event):
        """Handler for SOS resolved events."""
        await self.send_json({
            "type": "sos.resolved",
            "payload": event["payload"],
        })

    @database_sync_to_async
    def _create_sos_alert(self, latitude, longitude, message):
        from .models import SOSAlert
        sos = SOSAlert.objects.create(
            user=self.user,
            latitude=latitude,
            longitude=longitude,
            message=message,
        )
        return sos.id

    @database_sync_to_async
    def _resolve_sos_alert(self, sos_id):
        from .models import SOSAlert
        SOSAlert.objects.filter(id=sos_id).update(status=SOSAlert.Status.RESOLVED)

    @database_sync_to_async
    def _get_timestamp(self):
        from django.utils import timezone
        return timezone.now()
