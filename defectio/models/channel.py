from __future__ import annotations

from typing import List
from typing import Optional
from typing import Text
from typing import TYPE_CHECKING
from typing import Union

from defectio.models.user import User
from defectio.types.payloads import DMChannelPayload

from . import abc
from .message import Message
from .mixins import Hashable

if TYPE_CHECKING:
    from ..types.payloads import ChannelPayload
    from ..state import ConnectionState
    from .server import Server

__all__ = (
    "TextChannel",
    "VoiceChannel",
    "DMChannel",
    "GroupChannel",
)


class TextChannel(abc.Messageable, abc.ServerChannel, Hashable):
    def __init__(self, *, state: ConnectionState, server: Server, data: ChannelPayload):
        self._state: ConnectionState = state
        self.id: str = data["_id"]
        self._type: str = data["channel_type"]
        self.server = server
        self._update(data)

    def __repr__(self) -> str:
        attrs = [
            ("id", self.id),
            ("name", self.name),
        ]
        joined = " ".join("%s=%r" % t for t in attrs)
        return f"<{self.__class__.__name__} {joined}>"

    def _update(self, data) -> None:
        self.name: str = data["name"]
        self.topic: Optional[str] = data.get("topic")
        # self.position: int = data["position"]
        # Does this need coercion into `int`? No idea yet.
        # self._type: int = data.get("type", self._type)
        # self.last_message_id: Optional[int] = utils._get_as_snowflake(
        #     data, "last_message_id"
        # )
        # self._fill_overwrites(data)

    def _get_channel(self) -> TextChannel:
        return self

    @property
    def type(self) -> str:
        """:class:`str`: The channel's type."""
        return self._type

    @property
    def last_message(self) -> Optional[Message]:
        """Fetches the last message from this channel in cache.

        The message might not be valid or point to an existing message.

        .. admonition:: Reliable Fetching
            :class: helpful
            For a slightly more reliable method of fetching the
            last message, consider using either :meth:`history`
            or :meth:`fetch_message` with the :attr:`last_message_id`
            attribute.

        Returns
        ---------
        Optional[:class:`Message`]
            The last message in this channel or ``None`` if not found.
        """
        return (
            self._state._get_message(self.last_message_id)
            if self.last_message_id
            else None
        )


class SavedMessageChannel(abc.Messageable):
    def __init__(self, data: ChannelPayload, state: ConnectionState):
        super().__init__(data, state)

    def _get_channel(self) -> SavedMessageChannel:
        return self


class DMChannel(abc.Messageable):
    def __init__(self, data: DMChannelPayload, state: ConnectionState):
        self._state = state
        self.id = data.get("_id")
        self.active = data.get("active")
        # if "last_message" in data:
        #     self.last_message = state.get_message(data.get("last_message").get("_id"))
        # else:
        #     self.last_message = None
        self._recipients = data.get("recipients")

    def _get_channel(self) -> DMChannel:
        return self

    @property
    def recipients(self) -> List[User]:
        return [self._state.get_user(user) for user in self._recipients]

    def __str__(self) -> str:
        if self.recipient:
            return f"Direct Message with {self.recipient}"
        return "Direct Message with Unknown User"

    def __repr__(self) -> str:
        return f"<DMChannel id={self.id} recipient={self.recipient!r}>"


class GroupChannel(abc.Messageable):
    def __init__(self, data: ChannelPayload, state: ConnectionState):
        super().__init__(data, state)
        self.id = data.get("_id")
        self._update(data)

    def _update(self, data: ChannelPayload) -> None:
        self.name = data.get("name")
        self.active = data.get("active")
        self._recipients = data.get("recipients")
        # self.last_message = Message(self._state, data.get("last_message"))

    def _get_channel(self) -> GroupChannel:
        return self

    @property
    def recipients(self) -> List[User]:
        return [self._state.get_user(user) for user in self._recipients]


class VoiceChannel(abc.Messageable):
    def __init__(self, state: ConnectionState, server: Server, data):
        self._state: ConnectionState = state
        self.id: str = data["_id"]
        self._type: str = data["channel_type"]
        self.server = server
        self._update(data)

    def _update(self, data) -> None:
        self.name: str = data["name"]
        self.topic: Optional[str] = data.get("topic")
        # self.position: int = data["position"]
        # Does this need coercion into `int`? No idea yet.
        # self._type: int = data.get("type", self._type)
        # self.last_message_id: Optional[int] = utils._get_as_snowflake(
        #     data, "last_message_id"
        # )
        # self._fill_overwrites(data)

    def _get_channel(self) -> VoiceChannel:
        return self


MessageableChannel = Union[TextChannel, DMChannel, GroupChannel, SavedMessageChannel]


def channel_factory(data: ChannelPayload) -> type[abc.Messageable]:
    # Literal["SavedMessage", "DirectMessage", "Group", "TextChannel", "VoiceChannel"]
    channel_type = data["channel_type"]
    if channel_type == "SavedMessage":
        return SavedMessageChannel
    elif channel_type == "DirectMessage":
        return DMChannel
    elif channel_type == "Group":
        return GroupChannel
    elif channel_type == "TextChannel":
        return TextChannel
    elif channel_type == "VoiceChannel":
        return VoiceChannel
    else:
        raise Exception
