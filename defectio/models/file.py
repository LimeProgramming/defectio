from __future__ import annotations

import io
import os
from typing import TYPE_CHECKING, Literal
from typing import Optional
from typing import Union

from defectio.models.mixins import Hashable

if TYPE_CHECKING:
    from ..state import ConnectionState
    from ..types.payloads import AttachmentPayload


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

    __slots__ = (
        "id",
        "tag",
        "filename",
        "width",
        "height",
        "content_type",
        "size",
        "_state",
    )

    def __init__(self, *, data: AttachmentPayload, state: ConnectionState):
        self.id: int = data["_id"]
        self.tag: Literal["attachments"] = data["tag"]
        self.filename: str = data["filename"]
        self.width: Optional[int] = data["metadata"].get("width")
        self.height: Optional[int] = data["metadata"].get("height")
        self.content_type: Optional[str] = data.get("content_type")
        self.size: int = data["size"]
        self._state: ConnectionState = state

    @property
    def url(self) -> str:
        """:class:`str`: URL of the attachment"""
        base_url = self._state.api_info["features"]["autumn"]["url"]

        return f"{base_url}/{self.tag}/{self.id}"

    @property
    def is_spoiler(self) -> bool:
        """:class:`bool`: Whether this attachment contains a spoiler."""
        return self.filename.startswith("SPOILER_")

    def __repr__(self) -> str:
        return f"<Attachment id={self.id} filename={self.filename!r} url={self.url!r}>"

    def __str__(self) -> str:
        return self.url or ""

    def to_dict(self) -> dict:
        result: dict = {
            "filename": self.filename,
            "id": self.id,
            "tag": self.tag,
            "size": self.size,
            "url": self.url,
            "spoiler": self.is_spoiler(),
        }
        if self.width:
            result["width"] = self.width
        if self.height:
            result["height"] = self.height
        if self.content_type:
            result["content_type"] = self.content_type
        return result


class AutumnID(Hashable):
    """
    Attributes
    ------------
    id: :class:`int`
        The atumn file ID.
    """

    __slots__ = "id"

    def __init__(self, *, data):
        self.id: str = data["id"]

    def __str__(self) -> str:
        return self.id or ""


class File:
    """Respresents a file about to be uploaded to revolt

    Parameters
    -----------
    file: Union[str, bytes, os.PathLike, io.BufferedIOBase]
        The name of the file or the content of the file in bytes, text files will be need to be encoded
    filename: Optional[str]
        The filename of the file when being uploaded, this will default to the name of the file if one exists
    spoiler: bool
        Determines if the file will be a spoiler, this prefexes the filename with `SPOILER_`
    """

    def __init__(
        self,
        file: Union[str, bytes, os.PathLike, io.BufferedIOBase],
        *,
        filename: Optional[str] = None,
        spoiler: bool = False,
    ):
        if isinstance(file, io.IOBase):
            if not (file.seekable() and file.readable()):
                raise ValueError(f"File buffer {file!r} must be seekable and readable")
            self.fp = file
            self._original_pos = file.tell()
            self._owner = False
        if isinstance(file, bytes):
            self.fp = io.BytesIO(file)
            self._original_pos = 0
            self._owner = True
        else:
            self.fp = open(file, "rb")
            self._original_pos = 0
            self._owner = True

        # aiohttp only uses two methods from IOBase
        # read and close, since I want to control when the files
        # close, I need to stub it so it doesn't close unless
        # I tell it to
        self._closer = self.fp.close
        self.fp.close = lambda: None

        if filename is None:
            if isinstance(file, str):
                _, self.filename = os.path.split(file)
            else:
                self.filename = getattr(file, "name", None)
        else:
            self.filename = filename

        if (
            spoiler
            and self.filename is not None
            and not self.filename.startswith("SPOILER_")
        ):
            self.filename = "SPOILER_" + self.filename

        self.spoiler = spoiler or (
            self.filename is not None and self.filename.startswith("SPOILER_")
        )

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
