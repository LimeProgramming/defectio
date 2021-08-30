from __future__ import annotations
from .abc import Messageable
import asyncio

from typing import TYPE_CHECKING, Optional
from .mixins import Hashable


if TYPE_CHECKING:
    from ..state import ConnectionState
    from ..types.payloads import MessageEventPayload
    from .channel import TextChannel


class Message(Hashable):
    def __init__(
        self, state: ConnectionState, channel: TextChannel, data: MessageEventPayload
    ):
        self._state: ConnectionState = state
        self.id: str = data["_id"]
        self.channel: TextChannel = channel
        self.content: str = data["content"]
        self.author: str = data["author"]

    def __repr__(self) -> str:
        name = self.__class__.__name__
        return f"<{name} id={self.id} channel={self.channel!r} type={self.type!r} author={self.author!r}"

    @property
    def server(self) -> str:
        return self.channel.server

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
