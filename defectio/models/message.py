from __future__ import annotations
from defectio.models.user import PartialUser
from .abc import Messageable
import asyncio

from typing import TYPE_CHECKING, Optional
from .mixins import Hashable


if TYPE_CHECKING:
    from ..state import ConnectionState
    from ..types.payloads import MessagePayload
    from ..types.websocket import MessageUpdate
    from .channel import MessageableChannel
    from .user import User


class Message(Hashable):
    def __init__(
        self, state: ConnectionState, channel: MessageableChannel, data: MessagePayload
    ):
        self._state: ConnectionState = state
        self.id = data.get("_id")
        self.channel = channel
        self.content = data.get("content")
        self.author_id = data.get("author")

    def __repr__(self) -> str:
        name = self.__class__.__name__
        return f"<{name} id={self.id} channel={self.channel!r} author={self.author!r}"

    @property
    def server(self) -> str:
        return self.channel.server

    @property
    def author(self) -> PartialUser:
        return self._state.get_user(self.author_id) or PartialUser(self.author_id)

    async def delete(self, *, delay: Optional[float] = None) -> None:
        if delay is not None:

            async def delete(delay: float):
                await asyncio.sleep(delay)
                await self._state.http.delete_message(self.channel.id, self.id)

            asyncio.create_task(delete(delay))
        else:
            await self._state.http.delete_message(self.channel.id, self.id)

    async def edit(self, content: str) -> Message:
        data = await self._state.http.edit_message(
            self.channel.id, self.id, content=content
        )
        message = Message(state=self._state, channel=self.channel, data=data)

        return message

    def _update(self, data: MessageUpdate) -> None:
        if "content" in data["data"]:
            self.content = data.get("data").get("content")
