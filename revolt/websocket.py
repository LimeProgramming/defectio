from __future__ import annotations

from typing import TYPE_CHECKING, Any
import logging
import asyncio

from aiohttp.http_websocket import WSMessage

from .message import Message

try:
    import orjson as json
except ImportError:
    import json

if TYPE_CHECKING:
    import aiohttp
    from .client import Client

logger = logging.getLogger("revolt")


class WebsocketHandler:
    def __init__(
        self,
        session: aiohttp.ClientSession,
        token: str,
        ws_url: str,
        client: Client,
    ):
        self.session = session
        self.token = token
        self.ws_url = ws_url
        self.websocket: aiohttp.ClientWebSocketResponse
        self._dispatch: Client.dispatch = client.dispatch
        self._discord_parsers = client._connection.parsers

    async def send_payload(self, payload: Any):
        await self.websocket.send_str(json.dumps(payload).decode("utf-8"))

    async def heartbeat(self):
        while not self.websocket.closed:
            await self.send_payload({"type": "Ping"})
            await asyncio.sleep(15)

    async def send_authenticate(self):
        payload = {"type": "Authenticate", "token": self.token}

        await self.send_payload(payload)

    async def start(self):
        self.websocket = await self.session.ws_connect(self.ws_url)

        await self.send_authenticate()

        # Keep alive every 15 seconds
        asyncio.create_task(self.heartbeat())

        async for msg in self.websocket:
            await self.received_message(msg)

    async def received_message(self, msg: WSMessage):
        msg = json.loads(msg.data)

        logger.debug("WebSocket Event: %s", msg)
        event = msg.get("type").lower()
        if event:
            self._dispatch("socket_event_type", event)

        data = msg
        try:
            func = self._discord_parsers[event]
        except KeyError:
            logger.debug("Unknown event %s.", event)
        else:
            func(data)
