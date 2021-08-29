from __future__ import annotations

from typing import TYPE_CHECKING, Text, Union, Optional
from . import abc

if TYPE_CHECKING:
    from .payloads import Channel as ChannelPayload
    from .state import ConnectionState
    from .server import Server


class Channel:
    def __init__(self, data: ChannelPayload, state: ConnectionState):
        self.state = state
        self.id = data["_id"]
        self.channel_type = data["channel_type"]

    def __repr__(self) -> str:
        attrs = [
            ("id", self.id),
            ("type", self.channel_type),
        ]
        joined = " ".join("%s=%r" % t for t in attrs)
        return f"<{self.__class__.__name__} {joined}>"


class SavedMessageChannel(Channel):
    def __init__(self, data: ChannelPayload, state: ConnectionState):
        super().__init__(data, state)


class DMChannel(Channel):
    def __init__(self, data: ChannelPayload, state: ConnectionState):
        super().__init__(data, state)


class GroupDMChannel(Channel):
    def __init__(self, data: ChannelPayload, state: ConnectionState):
        super().__init__(data, state)


class TextChannel(abc.Messageable):
    """Represents a Discord guild text channel.
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
        # self._type: str = data["type"]
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


class VoiceChannel(Channel):
    def __init__(self, data: ChannelPayload, state: ConnectionState):
        super().__init__(data, state)


def channel_factory(data: ChannelPayload) -> type[Channel]:
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
