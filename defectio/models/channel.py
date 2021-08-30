from __future__ import annotations

from typing import Optional
from typing import Text
from typing import TYPE_CHECKING
from typing import Union

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
    """Represents a server text channel.
    .. container:: operations
        .. describe:: x == y
            Checks if two channels are equal.
        .. describe:: x != y
            Checks if two channels are not equal.
        .. describe:: hash(x)
            Returns the channel's hash.
        .. describe:: str(x)
            Returns the channel's name.
    Attributes
    -----------
    name: :class:`str`
        The channel name.
    guild: :class:`Guild`
        The guild the channel belongs to.
    id: :class:`int`
        The channel ID.
    category_id: Optional[:class:`int`]
        The category channel ID this channel belongs to, if applicable.
    topic: Optional[:class:`str`]
        The channel's topic. ``None`` if it doesn't exist.
    position: :class:`int`
        The position in the channel list. This is a number that starts at 0. e.g. the
        top channel is position 0.
    last_message_id: Optional[:class:`int`]
        The last message ID of the message sent to this channel. It may
        *not* point to an existing or valid message.
    slowmode_delay: :class:`int`
        The number of seconds a member must wait between sending messages
        in this channel. A value of `0` denotes that it is disabled.
        Bots and users with :attr:`~Permissions.manage_channels` or
        :attr:`~Permissions.manage_messages` bypass slowmode.
    nsfw: :class:`bool`
        If the channel is marked as "not safe for work".
        .. note::
            To check if the channel or the guild of that channel are marked as NSFW, consider :meth:`is_nsfw` instead.
    default_auto_archive_duration: :class:`int`
        The default auto archive duration in minutes for threads created in this channel.
        .. versionadded:: 2.0
    """

    __slots__ = (
        "name",
        "id",
        "server",
        "topic",
        "_state",
        "nsfw",
        "category_id",
        "position",
        "slowmode_delay",
        "_overwrites",
        "_type",
        "last_message_id",
        "default_auto_archive_duration",
    )

    def __init__(self, *, state: ConnectionState, server: Server, data):
        self._state: ConnectionState = state
        self.id: str = data["_id"]
        self._type: str = data["channel_type"]
        self._update(server, data)

    def __repr__(self) -> str:
        attrs = [
            ("id", self.id),
            ("name", self.name),
        ]
        joined = " ".join("%s=%r" % t for t in attrs)
        return f"<{self.__class__.__name__} {joined}>"

    def _update(self, server, data) -> None:
        self.server = server
        self.name: str = data["name"]
        self.topic: Optional[str] = data.get("topic")
        # self.position: int = data["position"]
        # Does this need coercion into `int`? No idea yet.
        # self._type: int = data.get("type", self._type)
        # self.last_message_id: Optional[int] = utils._get_as_snowflake(
        #     data, "last_message_id"
        # )
        # self._fill_overwrites(data)

    async def _get_channel(self):
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


class DMChannel(abc.Messageable):
    def __init__(self, data: ChannelPayload, state: ConnectionState):
        super().__init__(data, state)


class GroupDMChannel(abc.Messageable):
    def __init__(self, data: ChannelPayload, state: ConnectionState):
        super().__init__(data, state)


class VoiceChannel(abc.Messageable):
    def __init__(self, state: ConnectionState, server: Server, data):
        self._state: ConnectionState = state
        self.id: str = data["_id"]
        self._type: str = data["channel_type"]
        self._update(server, data)

    def _update(self, server, data) -> None:
        self.server = server
        self.name: str = data["name"]
        self.topic: Optional[str] = data.get("topic")
        # self.position: int = data["position"]
        # Does this need coercion into `int`? No idea yet.
        # self._type: int = data.get("type", self._type)
        # self.last_message_id: Optional[int] = utils._get_as_snowflake(
        #     data, "last_message_id"
        # )
        # self._fill_overwrites(data)


MessageableChannel = Union[TextChannel, DMChannel, GroupDMChannel, SavedMessageChannel]


def channel_factory(data: ChannelPayload) -> type[abc.Messageable]:
    # Literal["SavedMessage", "DirectMessage", "Group", "TextChannel", "VoiceChannel"]
    channel_type = data["channel_type"]
    if channel_type == "SavedMessage":
        return SavedMessageChannel
    elif channel_type == "DirectMessage":
        return DMChannel
    elif channel_type == "Group":
        return GroupDMChannel
    elif channel_type == "TextChannel":
        return TextChannel
    elif channel_type == "VoiceChannel":
        return VoiceChannel
    else:
        raise Exception
