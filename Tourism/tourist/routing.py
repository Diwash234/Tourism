"""
WebSocket URL routing for real-time features.

Routes:
- /ws/notifications/ — NotificationConsumer (real-time notifications)
- /ws/location/<trip_id>/ — LocationSharingConsumer (trip location sharing)
- /ws/sos/ — SOSAlertConsumer (emergency alerts)

All consumers expect a JWT token as a query parameter: ?token=<jwt>
"""

from django.urls import re_path

from . import consumers

websocket_urlpatterns = [
    re_path(r"^ws/notifications/$", consumers.NotificationConsumer.as_asgi()),
    re_path(r"^ws/location/(?P<trip_id>\d+)/$", consumers.LocationSharingConsumer.as_asgi()),
    re_path(r"^ws/sos/$", consumers.SOSAlertConsumer.as_asgi()),
]
