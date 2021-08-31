from __future__ import annotations

import asyncio
import copy
import sys
from typing import Any
from typing import Dict
from typing import Optional
from typing import Protocol
from typing import runtime_checkable
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..state import ConnectionState
    from .server import Server


@runtime_checkable
class User(Protocol):
    """An ABC that details the common operations on a Revolt user.
    The following implement this ABC:
    - :class:`~defectio.User`
    - :class:`~defectio.ClientUser`
    - :class:`~defectio.Member`
    Attributes
    -----------
    name: :class:`str`
        The user's username.
    bot: :class:`bool`
        If the user is a bot account.
    """

    __slots__ = ()

    name: str
    bot: bool

    @property
    def display_name(self) -> str:
        """:class:`str`: Returns the user's display name."""
        raise NotImplementedError

    @property
    def mention(self) -> str:
        """:class:`str`: Returns a string that allows you to mention the given user."""
        raise NotImplementedError


class ServerChannel:
    __slots__ = ()

    id: int
    name: str
    server: Server
    type: str
    position: int
    category_id: Optional[int]
    _state: ConnectionState

    if TYPE_CHECKING:

        def __init__(
            self, *, state: ConnectionState, server: Server, data: Dict[str, Any]
        ):
            ...

    def __str__(self) -> str:
        return self.name

    def _update(self, server: Server, data: Dict[str, Any]) -> None:
        raise NotImplementedError

    async def delete(self, *, reason: Optional[str] = None) -> None:
        await self._state.http.close_channel(self.id)


class Messageable(Protocol):

    __slots__ = ()
    _state: ConnectionState

    async def _get_channel(self):
        raise NotImplementedError

    async def send(
        self,
        content: str = None,
        *,
        file=None,
        files=None,
        delete_after: int = None,
        nonce=None,
    ):

        channel = await self._get_channel()
        state = self._state
        content = str(content) if content is not None else None

        # if mention_author is not None:
        #     allowed_mentions = allowed_mentions or AllowedMentions().to_dict()
        #     allowed_mentions["replied_user"] = bool(mention_author)

        # if reference is not None:
        #     try:
        #         reference = reference.to_message_reference_dict()
        #     except AttributeError:
        #         raise InvalidArgument(
        #             "reference parameter must be Message or MessageReference"
        #         ) from None

        # if file is not None and files is not None:
        #     raise InvalidArgument("cannot pass both file and files parameter to send()")

        # if file is not None:
        #     if not isinstance(file, File):
        #         raise InvalidArgument("file parameter must be File")

        #     try:
        #         data = await state.http.send_files(
        #             channel.id,
        #             files=[file],
        #             allowed_mentions=allowed_mentions,
        #             content=content,
        #             embed=embed,
        #             nonce=nonce,
        #             message_reference=reference,
        #         )
        #     finally:
        #         file.close()

        # elif files is not None:
        #     if len(files) > 10:
        #         raise InvalidArgument(
        #             "files parameter must be a list of up to 10 elements"
        #         )
        #     elif not all(isinstance(file, File) for file in files):
        #         raise InvalidArgument("files parameter must be a list of File")

        #     try:
        #         data = await state.http.send_files(
        #             channel.id,
        #             files=files,
        #             content=content,
        #             tts=tts,
        #             embed=embed,
        #             nonce=nonce,
        #             allowed_mentions=allowed_mentions,
        #             message_reference=reference,
        #         )
        #     finally:
        #         for f in files:
        #             f.close()
        # else:
        data = await state.http.send_message(
            channel.id,
            content,
        )

        ret = state.create_message(channel=channel, data=data)
        if delete_after is not None:
            await ret.delete(delay=delete_after)
        return ret

    async def fetch_message(self, id):
        channel = await self._get_channel()
        data = await self._state.http.get_message(channel.id, id)
        return self._state.create_message(channel=channel, data=data)

    async def start_typing(self):
        channel = await self._get_channel()
        await self._state.websocket.begin_typing(channel.id)

    async def stop_typing(self):
        channel = await self._get_channel()
        await self._state.websocket.stop_typing(channel.id)
