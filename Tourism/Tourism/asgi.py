"""
ASGI config for Tourism project.

HTTP is served by the standard Django application; WebSocket traffic for
the live chat (master spec §30) and real-time features (notifications,
location sharing, SOS alerts) is routed to channels consumers.
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Tourism.settings')

# Initialize Django before importing consumers/routing (channels requirement).
django_asgi_app = get_asgi_application()

from channels.routing import ProtocolTypeRouter, URLRouter  # noqa: E402
from django.urls import path  # noqa: E402

from chatbot.consumers import ChatConsumer  # noqa: E402
from tourist.routing import websocket_urlpatterns  # noqa: E402

# channels' URLRouter raises ImproperlyConfigured on include() (it needs
# nested URLRouter instances), and tourist.routing exposes
# websocket_urlpatterns rather than urlpatterns. Both route lists already
# carry the full "ws/..." prefix, so splice them into one flat router.
application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": URLRouter([
        path("ws/chat/<int:conversation_id>/", ChatConsumer.as_asgi()),
        *websocket_urlpatterns,
    ]),
})
