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
