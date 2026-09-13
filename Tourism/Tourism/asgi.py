"""
ASGI config for Tourism project.

HTTP is served by the standard Django application; WebSocket traffic for
the live chat (master spec §30) is routed to channels consumers.
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Tourism.settings')

# Initialize Django before importing consumers/routing (channels requirement).
django_asgi_app = get_asgi_application()

from channels.routing import ProtocolTypeRouter, URLRouter  # noqa: E402
from django.urls import path  # noqa: E402

from chatbot.consumers import ChatConsumer, SupportInboxConsumer  # noqa: E402

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": URLRouter([
        path("ws/chat/<int:conversation_id>/", ChatConsumer.as_asgi()),
        path("ws/support/", SupportInboxConsumer.as_asgi()),
    ]),
})
