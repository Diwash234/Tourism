"""
WebSocket consumer for live chat (master spec §30).

Full-duplex channel per conversation: the REST POST endpoint keeps being
the source of truth for sending messages, while this socket pushes new
messages (user + assistant, with cards) to every connected client of the
same conversation — multiple tabs/devices stay in sync without polling.
Anonymous visitors are allowed (conversations are keyed by id/session on
the REST side); the socket only ever broadcasts messages that the REST
API already persisted, so nothing new is exposed.
"""

import asyncio

from channels.generic.websocket import AsyncJsonWebsocketConsumer

# Event loop the WebSocket consumers run on (daphne/uvicorn main loop).
# Sync REST views broadcast from worker threads, so they must schedule
# group sends onto THIS loop — the in-memory layer's queues are bound to it.
_MAIN_LOOP = {"loop": None}


def get_main_loop():
    return _MAIN_LOOP["loop"]


class ChatConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        _MAIN_LOOP["loop"] = asyncio.get_running_loop()
        self.conversation_id = self.scope["url_route"]["kwargs"]["conversation_id"]
        self.group_name = f"chat_{self.conversation_id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        await self.send_json({"type": "chat.connected", "conversation_id": int(self.conversation_id)})

    async def disconnect(self, code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive_json(self, content, **kwargs):
        # Clients may ping to keep the socket warm through proxies.
        if content.get("type") == "ping":
            await self.send_json({"type": "pong"})

    async def chat_message(self, event):
        """Fan-out handler for events sent via channel_layer.group_send."""
        await self.send_json(event["payload"])


class SupportInboxConsumer(AsyncJsonWebsocketConsumer):
    """Admin/staff live support inbox.

    Joins the `support_inbox` group: every user chat message is fanned out
    here so the admin dashboard sees new messages within seconds (no
    polling). REST stays the source of truth — this socket only relays
    events the API already persisted.
    """

    GROUP = "support_inbox"

    async def connect(self):
        _MAIN_LOOP["loop"] = asyncio.get_running_loop()
        # Auth: JWT via ?token= (frontend stores JWT in localStorage, not
        # cookies) or an authenticated session user when middleware provides one.
        user = self.scope.get("user")
        if not (user and user.is_authenticated):
            from urllib.parse import parse_qs
            qs = parse_qs(self.scope.get("query_string", b"").decode())
            token = (qs.get("token") or [""])[0]
            if token:
                try:
                    from rest_framework_simplejwt.tokens import AccessToken
                    from django.contrib.auth import get_user_model
                    validated = AccessToken(token)
                    user = get_user_model().objects.filter(pk=validated["user_id"]).first()
                except Exception:
                    user = None
        is_staff = bool(user and getattr(user, "is_authenticated", False) and (
            user.is_staff or getattr(user, "role", "") in {"admin", "super_admin", "tourism_admin", "content_moderator", "staff"}))
        if not is_staff:
            await self.close(code=4403)
            return
        await self.channel_layer.group_add(self.GROUP, self.channel_name)
        await self.accept()
        await self.send_json({"type": "support.connected"})

    async def disconnect(self, code):
        await self.channel_layer.group_discard(self.GROUP, self.channel_name)

    async def receive_json(self, content, **kwargs):
        if content.get("type") == "ping":
            await self.send_json({"type": "pong"})

    async def chat_message(self, event):
        await self.send_json(event["payload"])
