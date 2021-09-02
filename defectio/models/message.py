from __future__ import annotations

import os
import io
import asyncio
from typing import(
    Union,
    Literal,
    Optional,
    TYPE_CHECKING,
)

from defectio.models.user import PartialUser

#from .abc import Messageable
from .mixins import Hashable



if TYPE_CHECKING:
    from ..state import ConnectionState
    from ..types.payloads import MessagePayload, AttachmentPayload, AutumnPayload
    from ..types.websocket import MessageUpdate
    from .channel import MessageableChannel
    from .user import User


class Attachment(Hashable):
    """
    Attributes
    ------------
    id: :class:`int`
        The attachment ID.
    tag: :class:`str`
        The attachment tag
    filename: :class:`str`
        The attachment's filename.
    width: Optional[:class:`int`]
        The attachment's width, in pixels. Only applicable to images and videos.
    height: Optional[:class:`int`]
        The attachment's height, in pixels. Only applicable to images and videos.
    size: :class:`int`
        The attachment size in bytes.
    url: :class:`str`
        The attachment URL. If the message this attachment was attached
        to is deleted, then this will 404.
    content_type: Optional[:class:`str`]
        The attachment's `media type <https://en.wikipedia.org/wiki/Media_type>`_
    """

    __slots__ = ('id', 'tag', 'filename', 'width', 'height', 'content_type', 'size', '_state')

    def __init__(self, *, data: AttachmentPayload, state: ConnectionState):
        self.id: int = data['_id']
        self.tag: Literal["attachments"] = data['tag']
        self.filename: str = data['filename']
        self.width: Optional[int] = data['metadata'].get('width')
        self.height: Optional[int] = data['metadata'].get('height')
        self.content_type: Optional[str] = data.get('content_type')
        self.size: int = data['size']
        self._state: ConnectionState = state

    @property
    def url(self) -> str:
        """:class:`str`: URL of the attachment"""
        base_url = self._state.api_info["features"]["autumn"]["url"]

        return f"{base_url}/{self.tag}/{self.id}"
    
    @property
    def is_spoiler(self) -> bool:
        """:class:`bool`: Whether this attachment contains a spoiler."""
        return self.filename.startswith('SPOILER_')

    def __repr__(self) -> str:
        return f'<Attachment id={self.id} filename={self.filename!r} url={self.url!r}>'

    def __str__(self) -> str:
        return self.url or ''

    def to_dict(self) -> dict:
        result: dict = {
            'filename': self.filename,
            'id': self.id,
            'tag': self.tag,
            'size': self.size,
            'url': self.url,
            'spoiler': self.is_spoiler(),
        }
        if self.width:
            result['width'] = self.width
        if self.height:
            result['height'] = self.height
        if self.content_type:
            result['content_type'] = self.content_type
        return result

class AutumnID(Hashable):
    """
    Attributes
    ------------
    id: :class:`int`
        The atumn file ID.
    """

    __slots__ = ('id')

    def __init__(self, *, data:AutumnPayload):
        self.id: str = data['id']

    def __str__(self) -> str:
        return self.id or ''


class File:
    """ Represents a file to be uploaded to Revolt. IE missing an Autumn ID value

    Parameters
    -----------
    file: Union[str, bytes]
        The name of the file or the content of the file in bytes, text files will be need to be encoded
    filename: Optional[str]
        The filename of the file when being uploaded, this will default to the name of the file if one exists
    spoiler: bool
        Determines if the file will be a spoiler, this prefexes the filename with `SPOILER_`
    """

    __slots__ = ('fp', 'filename', 'spoiler', '_original_pos', '_owner', '_closer')

    def __init__(
        self,
        fp: Union[str, bytes, os.PathLike, io.BufferedIOBase],
        filename: Optional[str] = None,
        *,
        spoiler: bool = False
    ):
        if isinstance(fp, io.IOBase):
            if not (fp.seekable() and fp.readable()):
                raise ValueError(f'File buffer {fp!r} must be seekable and readable')
            self.fp = fp
            self._original_pos = fp.tell()
            self._owner = False
        else:
            self.fp = open(fp, 'rb')
            self._original_pos = 0
            self._owner = True


        # aiohttp only uses two methods from IOBase
        # read and close, since I want to control when the files
        # close, I need to stub it so it doesn't close unless
        # I tell it to
        self._closer = self.fp.close
        self.fp.close = lambda: None


        if filename is None:
            if isinstance(fp, str):
                _, self.filename = os.path.split(fp)
            else:
                self.filename = getattr(fp, 'name', None)
        else:
            self.filename = filename


        if spoiler and self.filename is not None and not self.filename.startswith('SPOILER_'):
            self.filename = 'SPOILER_' + self.filename

        self.spoiler = spoiler or (self.filename is not None and self.filename.startswith('SPOILER_'))


    def reset(self, *, seek: Union[int, bool] = True) -> None:
        # The `seek` parameter is needed because
        # the retry-loop is iterated over multiple times
        # starting from 0, as an implementation quirk
        # the resetting must be done at the beginning
        # before a request is done, since the first index
        # is 0, and thus false, then this prevents an
        # unnecessary seek since it's the first request
        # done.
        if seek:
            self.fp.seek(self._original_pos)

    def close(self) -> None:
        self.fp.close = self._closer
        if self._owner:
            self._closer()

    #async def from_url(self, url: str) -> Optional[File]:
    #    async with self._state.http._session.get(url) as resp:
    #        resp.raise_for_status()
    #        data = io.BytesIO(await resp.read())

    #    return File(self._state, data)


class Message(Hashable):
    def __init__(
        self, state: ConnectionState, channel: MessageableChannel, data: MessagePayload
    ):
        self._state: ConnectionState = state
        self.id = data.get("_id")
        self.channel = channel
        self.content = data.get("content")
        self.author_id = data.get("author")
        self.attachments = [Attachment(state=state, data=a) for a in data.get("attachments", [])]

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
