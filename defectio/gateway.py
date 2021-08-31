from __future__ import annotations

import asyncio
from defectio.errors import LoginFailure
import logging
from typing import Any, Union
from typing import TYPE_CHECKING
from .types.websocket import Authenticated, Error

import aiohttp

import orjson as json

if TYPE_CHECKING:
    from defectio.client import Client

logger = logging.getLogger("defectio")


class DefectioWebsocket:
    def __init__(
        self,
        session: aiohttp.ClientSession,
        ws_url: str,
        user_agent: str,
        client: Client,
    ) -> None:
        self.session = session
        self.ws_url = ws_url
        self.websocket: aiohttp.ClientWebSocketResponse
        self._dispatch: Client.dispatch = client.dispatch
        self._parsers = client._connection.parsers
        self.user_agent = user_agent

        self.token: str

    @property
    def closed(self) -> bool:
        return self.websocket.closed

    async def send_payload(self, payload: Any) -> None:
        await self.websocket.send_str(json.dumps(payload).decode("utf-8"))

    async def wait_for_auth(self) -> Union[Error, Authenticated]:
        auth_event = await self.websocket.receive()
        response: Union[Error, Authenticated]
        if auth_event.type == aiohttp.WSMsgType.TEXT:
            payload = json.loads(auth_event.data)
            if payload.get("type") == "Authenticated":
                response = Authenticated(payload)
            else:
                response = Error(payload)
        return response

    async def send_authenticate(self) -> None:
        payload = {"type": "Authenticate", "token": self.token}
        await self.send_payload(payload)
        try:
            authenticated = await asyncio.wait_for(self.wait_for_auth(), timeout=10)
        except asyncio.TimeoutError:
            authenticated = Error({"type": "InternalError", "error": "timeout"})
        if authenticated["type"] != "Authenticated":
            logger.error("Authentication failed.")
            raise LoginFailure(authenticated)

        logger.info("Websocket connected and authenticated.")

    async def connect(self, token: str) -> None:
        self.token = token
        kwargs = {
            "max_msg_size": 0,
            "timeout": 30.0,
            "autoclose": False,
            "headers": {
                "User-Agent": self.user_agent,
            },
            "compress": 0,
        }
        self.websocket = await self.session.ws_connect(
            self.ws_url, heartbeat=15, **kwargs
        )

        logger.debug("Websocket connected to %s", self.ws_url)

        await self.send_authenticate()

        async for msg in self.websocket:
            await self.received_message(msg)

    async def received_message(self, msg: aiohttp.http_websocket.WSMessage) -> None:
        payload = json.loads(msg.data)

        logger.debug("WebSocket Event: %s", msg)
        event = payload.get("type").lower()
        if event:
            self._dispatch("socket_event_type", event)

        try:
            func = self._parsers[event]
        except KeyError:
            logger.debug("Unknown event %s.", event)
        else:
            func(payload)

    async def begin_typing(self, channel: str) -> None:
        payload = {"type": "BeginTyping", "channel": channel}
        await self.send_payload(payload)

    async def stop_typing(self, channel: str) -> None:
        payload = {"type": "StopTyping", "channel": channel}
        await self.send_payload(payload)

    async def ping(self) -> None:
        payload = {"type": "Ping"}
        await self.send_payload(payload)
