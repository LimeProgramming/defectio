from __future__ import annotations

import asyncio
from typing import Optional
from typing import TYPE_CHECKING

from defectio.models.user import PartialUser

from .abc import Messageable
from .mixins import Hashable
import io


if TYPE_CHECKING:
    from ..state import ConnectionState
    from ..types.payloads import MessagePayload, AttachmentPayload
    from ..types.websocket import MessageUpdate
    from .channel import MessageableChannel
    from .user import User


class Attachment:
    def __init__(self, state: ConnectionState, data: AttachmentPayload):
        self._state: ConnectionState = state
        self.id = data.get("_id")
        self.tag = data.get("tag")
        self.size = data.get("size")
        self.filename = data.get("filename")
        self.content_type = data.get("content_type")
        self.metadata_type = data.get("metadata").get("type")

    @property
    def url(self) -> str:
        base_url = self._state.api_info["features"]["autumn"]["url"]

        return f"{base_url}/{self.tag}/{self.id}"


class File:
    def __init__(self, file: io.BytesIO, name: str) -> None:
        self._file = file
        self.name = name

    async def from_url(self, url: str) -> Optional[File]:
        async with self._state.http._session.get(url) as resp:
            resp.raise_for_status()
            data = io.BytesIO(await resp.read())

        return File(self._state, data)


class Message(Hashable):
    def __init__(
        self, state: ConnectionState, channel: MessageableChannel, data: MessagePayload
    ):
        self._state: ConnectionState = state
        self.id = data.get("_id")
        self.channel = channel
        self.content = data.get("content")
        self.author_id = data.get("author")
        self.attachments = [Attachment(state, a) for a in data.get("attachments", [])]

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
        await self._state.http.edit_message(self.channel.id, self.id, content=content)
        self.content = content

        return self

    def _update(self, data: MessageUpdate) -> None:
        if "content" in data["data"]:
            self.content = data.get("data").get("content")
