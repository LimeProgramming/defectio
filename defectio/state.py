from __future__ import annotations

import asyncio
import copy
import inspect
import logging
from collections import deque
from collections import OrderedDict
from typing import Any
from typing import Callable
from typing import Deque
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple
from typing import TYPE_CHECKING
from typing import Union

from defectio.gateway import DefectioWebsocket
from defectio.http import DefectioHTTP
from defectio.models.abc import Messageable
from defectio.models.auth import Auth
from defectio.models.channel import DMChannel
from defectio.models.channel import GroupChannel
from defectio.models.channel import TextChannel
from defectio.models.member import PartialMember

from . import utils
from .models import channel_factory
from .models import Member
from .models import Message
from .models import MessageableChannel
from .models import Server
from .models import User
from .models import VoiceChannel
from .models.apiinfo import ApiInfo
from .models.raw_models import RawMessageDeleteEvent
from .models.raw_models import RawMessageUpdateEvent

if TYPE_CHECKING:
    from . import abc
    from .types.websocket import (
        Authenticated,
        ChannelAck as ChannelAckPayload,
        ChannelCreate,
        ChannelDelete,
        ChannelGroupJoin,
        ChannelGroupLeave,
        ChannelStartTyping,
        ChannelStopTyping,
        ChannelUpdate,
        MessageDelete,
        MessageUpdate,
        Pong,
        Ready,
        ServerDelete,
        ServerMemberJoin,
        ServerMemberLeave,
        ServerMemberUpdate,
        ServerRoleDelete,
        ServerRoleUpdate,
        ServerUpdate,
        UserRelationship,
        UserUpdate,
        Message as MessagePayload,
    )

    from .types.payloads import (
        UserPayload,
        ServerPayload,
        ChannelPayload,
        MemberPayload,
        BasicMemberPayload,
        ApiInfoPayload,
    )

    Channel = Union[DMChannel, GroupChannel, TextChannel, VoiceChannel]

logger = logging.getLogger("defectio")


class ConnectionState:
    def __init__(
        self,
        dispatch: Callable,
        handlers: Dict[str, Callable],
        http: Callable[[], DefectioHTTP],
        websocket: Callable[[], DefectioWebsocket],
        auth: Auth,
        loop: asyncio.AbstractEventLoop,
        **options: Any,
    ) -> None:
        """Initialize a new connection state

        Parameters
        ----------
        dispatch : Callable
            Callback to dispatch a message to a handler
        handlers : Dict[str, Callable]
            Mapping of message type to handler functions
        http : Callable[[], DefectioHTTP]
            HTTP request handler
        websocket : Callable[[], DefectioWebsocket]
            Websocket request handler
        auth : Auth
            Authentication details
        loop : asyncio.AbstractEventLoop
            Event loop to use
        """
        self.get_http = http
        self.get_websocket = websocket
        self.auth = auth
        self.handlers: Dict[str, Callable] = handlers
        self.dispatch: Callable = dispatch
        self.max_messages: Optional[int] = options.get("max_messages", 1000)
        self.loop: asyncio.AbstractEventLoop = loop
        self.parsers: Dict[str, Callable[[Dict[str, Any]], None]] = {}

        for attr, func in inspect.getmembers(self):
            if attr.startswith("parse_"):
                self.parsers[attr[6:]] = func

        self.clear()

    def clear(self) -> None:
        """Clear all data from the internal cache and reset the connection state."""
        self.user_id: Optional[str] = None
        self.api_info: Optional[ApiInfoPayload] = None
        self._servers: Dict[str, Server] = {}
        self._users: Dict[str, User] = {}
        self._server_channels: Dict[str, List[Channel]] = {}
        self._members: Dict[str, List[Member]] = {}
        self._private_channels: OrderedDict[str, PrivateChannel] = OrderedDict()
        self._private_channels_by_user: Dict[str, DMChannel] = {}
        if self.max_messages is not None:
            self._messages: Optional[Deque[Message]] = deque(maxlen=self.max_messages)
        else:
            self._messages: Optional[Deque[Message]] = None

    def call_handlers(self, key: str, *args: Any, **kwargs: Any) -> None:
        """Call the handler for the key

        Parameters
        ----------
        key : str
            Key to call the handler for
        """
        try:
            func = self.handlers[key]
        except KeyError:
            pass
        else:
            func(*args, **kwargs)

    def set_api_info(self, api_info: ApiInfoPayload) -> ApiInfo:
        """Set the API info

        Parameters
        ----------
        api_info : ApiInfoPayload
            API info payload

        Returns
        -------
        ApiInfo
            API info object
        """
        api_info = ApiInfo(api_info)
        self.api_info = api_info
        return api_info

    @property
    def self_id(self) -> Optional[str]:
        u = self.user
        return u.id if u else None

    @property
    def http(self) -> DefectioHTTP:
        return self.get_http()

    @property
    def websocket(self) -> DefectioWebsocket:
        return self.get_websocket()

    @property
    def user(self) -> User:
        """Get the user object

        Returns
        -------
        User
            The user object
        """
        return self.get_user(self.user_id)

    @property
    def users(self) -> List[User]:
        """Get all users from internal cache

        Returns
        -------
        List[User]
            List of users
        """
        return list(self._users.values())

    def get_user(self, user_id: Optional[str]) -> Optional[User]:
        """Get user from internal cache

        Parameters
        ----------
        user_id : Optional[str]
            User ID to get

        Returns
        -------
        Optional[User]
            User object from the cache
        """
        return self._users.get(user_id)

    def _add_user(self, user: User) -> None:
        """Add a user in internal cache

        Parameters
        ----------
        user : User
            User object to add
        """
        self._users[user.id] = user

    def _add_user_from_data(self, data: UserPayload) -> User:
        """Add a user in internal cache

        Parameters
        ----------
        data : UserPayload
            User data

        Returns
        -------
        User
            User object from the provided data
        """
        user = User(state=self, data=data)
        self._add_user(user)
        return user

    def _remove_user(self, user_id: str) -> None:
        """Remove a user from internal cache

        Parameters
        ----------
        user_id : str
            User ID to remove
        """
        del self._users[user_id]

    @property
    def servers(self) -> List[Server]:
        return list(self._servers.values())

    def get_server(self, server_id: Optional[str]) -> Optional[Server]:
        """Get a server by ID

        Parameters
        ----------
        server_id : Optional[str]
            Server ID

        Returns
        -------
        Optional[Server]
            Server object
        """
        return self._servers.get(server_id)

    def _add_server(self, server: Server) -> None:
        """Add a server to the internal cache

        Parameters
        ----------
        server : Server
            Server to add
        """
        self._servers[server.id] = server

    def _add_server_from_data(self, data: ServerPayload) -> Server:
        """Add a server to the internal cache from raw data

        Parameters
        ----------
        data : ServerPayload
            Server data

        Returns
        -------
        Server
            Server object from the provided data
        """
        server = Server(data=data, state=self)
        self._add_server(server)
        return server

    def _remove_server(self, server: Server) -> None:
        """Remove a server from the internal cache

        Parameters
        ----------
        server : Server
            Server to remove
        """
        self._servers.pop(server.id, None)

        for channel in server.channels:
            self._remove_channel(channel)

        del server

    @property
    def channels(self) -> List[Channel]:
        return list(self._server_channels.values())

    def get_channel(self, channel_id: str) -> Optional[Channel]:
        """Get a channel from the cache

        Parameters
        ----------
        channel_id : str
            ID of the channel to get

        Returns
        -------
        Optional[Channel]
            Channel object from the cache
        """

        channel = self._server_channels.get(channel_id)
        return channel

    def _add_channel(self, channel: Channel) -> None:
        """Add a channel to the internal cache

        Parameters
        ----------
        channel : Channel
            Channel to add
        """
        self._server_channels[channel.id] = channel

    def _add_channel_from_data(self, data: ChannelPayload) -> Channel:
        """Add a channel to the internal cache from raw data

        Parameters
        ----------
        data : ChannelPayload
            Channel data

        Returns
        -------
        Channel
            Channel object from the provided data
        """
        cls = channel_factory(data)
        server = self.get_server(data.get("server"))
        if server is not None:
            channel = cls(state=self, data=data, server=server)
        else:
            channel = cls(state=self, data=data)
        self._add_channel(channel)
        return channel

    def _remove_channel(self, channel: Channel) -> None:
        """Remove a channel from the internal cache

        Parameters
        ----------
        channel : Channel
            Channel to remove
        """
        self._server_channels.pop(channel.id, None)

        del channel

    @property
    def messages(self) -> Optional[List[Message]]:
        return list(self._messages)

    def get_message(self, msg_id: Optional[str]) -> Optional[Message]:
        """Get a message from the cache

        Parameters
        ----------
        msg_id : Optional[str]
            ID of the message to get

        Returns
        -------
        Optional[Message]
            Message from the cache
        """
        return (
            utils.find(lambda m: m.id == msg_id, reversed(self._messages))
            if self._messages
            else None
        )

    def _add_message(self, message: Message) -> None:
        """Add a message to the internal cache

        Parameters
        ----------
        message : Message
            Message to add
        """
        self._messages.append(message)

    def _add_message_from_data(self, data: MessagePayload) -> Message:
        """Add a message to the internal cache from raw data

        Parameters
        ----------
        data : MessagePayload
            Message data

        Returns
        -------
        Message
            Message object from the provided data
        """
        server = self.get_server(data.get("server"))
        channel = self.get_channel(data.get("channel"))
        message = Message(data=data, state=self, channel=channel)
        self._add_message(message)
        return message

    def _remove_message(self, message: Message) -> None:
        """Remove a message from the internal cache

        Parameters
        ----------
        message : Message
            Message to remove
        """
        self._messages.remove(message)

        del message

    @property
    def members(self) -> List[Member]:
        return list(self._members.values())

    def get_member(self, member_id: str) -> Optional[Member]:
        """Get a member from the cache

        Parameters
        ----------
        member_id : str
            ID of the member to get

        Returns
        -------
        Optional[Member]
            Member object from the cache
        """
        return self._members.get(member_id)

    def _add_member(self, member: Union[Member, PartialMember]) -> None:
        """Add a member to the internal cache

        Parameters
        ----------
        member : Union[Member, PartialMember]
            Member to add
        """
        self._members[member.id] = member

    def _add_member_from_data(
        self, data: Union[MemberPayload, BasicMemberPayload]
    ) -> Union[Member, PartialMember]:
        """Add a member to the internal cache from raw data

        Parameters
        ----------
        data : Union[MemberPayload, BasicMemberPayload]
            Member data

        Returns
        -------
        Union[Member, PartialMember]
            Member object from the provided data
        """
        if "user" in data:
            member = PartialMember(data["user"], self)
        else:
            member = Member(data, self)
        self._add_member(member)
        return member

    def _remove_member(self, member: Union[Member, PartialMember]) -> None:
        """Remove a member from the internal cache

        Parameters
        ----------
        member : Union[Member, PartialMember]
            Member to remove
        """
        self._members[member.server.id].pop(member.id, None)

        del member

    def parse_ready(self, data: Ready) -> None:
        self.clear()

        for user in data["users"]:
            self._add_user_from_data(user)

        if self.auth().is_bot:
            self.user_id = data["users"][0]["_id"]
        else:
            self.user_id = self.auth().user_id

        for server in data["servers"]:
            self._add_server_from_data(server)

        for channel in data["channels"]:
            self._add_channel_from_data(channel)

        for member in data["members"]:
            self._add_member_from_data(member)

        self.call_handlers("ready")
        self.dispatch("ready")

    def parse_message(self, data: MessagePayload) -> None:
        message = self._add_message_from_data(data)
        self.dispatch("message", message)
        if self._messages is not None:
            self._messages.append(message)

    def parse_messageupdate(self, data: MessageUpdate) -> None:
        raw = RawMessageUpdateEvent(data)
        message = self.get_message(raw.message_id)
        if message is not None:
            older_message = copy.copy(message)
            raw.cached_message = older_message
            self.dispatch("raw_message_edit", raw)
            message._update(data)
            self.dispatch("message_edit", older_message, message)
        else:
            self.dispatch("raw_message_edit", raw)

    def parse_messagedelete(self, data: MessageDelete) -> None:
        raw = RawMessageDeleteEvent(data)
        found = self.get_message(data["id"])
        raw.cached_message = found
        self.dispatch("raw_message_delete", raw)
        if self._messages is not None and found is not None:
            self.dispatch("message_delete", found)
            self._messages.remove(found)

    def parse_channelcreate(self, data: ChannelCreate) -> None:
        channel = self._add_channel_from_data(data)
        self.dispatch("channel_create", channel)

    def parse_channelupdate(self, data: ChannelUpdate) -> None:
        channel = self.get_channel(data["_id"])
        if channel is not None:
            channel._update(data)
            self.dispatch("channel_update", channel)
        self.dispatch("channel_update", data)

    def parse_channeldelete(self, data: ChannelDelete) -> None:
        channel = self.get_channel(data["id"])
        channel_copy = copy.copy(channel)
        self._remove_channel(channel)
        self.dispatch("channel_delete", channel_copy)

    def parse_channelgroupjoin(self, data: ChannelGroupJoin) -> None:
        self.dispatch("channel_group_join", data)

    def parse_channelgroupleave(self, data: ChannelGroupLeave) -> None:
        channel = self.get_channel(data["channel"])
        channel_copy = copy.copy(channel)
        self._remove_channel(channel)
        self.dispatch("channel_group_leave", channel_copy)

    def parse_channelstarttyping(self, data: ChannelStartTyping) -> None:
        channel = self.get_channel(data["id"])
        user = self.get_user(data["user"])
        self.dispatch("channel_start_typing", channel, user)

    def parse_channelstoptyping(self, data: ChannelStopTyping) -> None:
        channel = self.get_channel(data["id"])
        user = self.get_user(data["user"])
        self.dispatch("channel_stop_typing", channel, user)

    def parse_channelack(self, data: ChannelAckPayload) -> None:
        self.dispatch("channel_ack", data)

    def parse_serverupdate(self, data: ServerUpdate) -> None:
        server = self.get_server(data["id"])
        if server is not None:
            old_server = copy.copy(server)
            server._update(data)
            self.dispatch("server_update", old_server, server)
        else:
            logger.debug(
                "SERVER_UPDATE referencing an unknown server ID: %s. Discarding.",
                data["id"],
            )

    def parse_serverdelete(self, data: ServerDelete) -> None:
        server = self.get_server(data["id"])
        if server is not None:
            self.servers.pop(server.id)
        self.dispatch("server_delete", server)

    def parse_servermemberjoin(self, data: ServerMemberJoin) -> None:
        member = self._add_member_from_data(data)
        self.dispatch("server_member_join", member)

    def parse_servermemberleave(self, data: ServerMemberLeave) -> None:
        member = self.get_member(data["server"], data["id"])
        self.members.get(data.get("id"), {}).pop(data.get("user"))
        self.dispatch("server_member_leave", member)

    def parse_servermemberupdate(self, data: ServerMemberUpdate) -> None:
        member = self.get_member(data["id"])
        if isinstance(member, Member):
            old_member = copy.copy(member)
            member._update(data)
            self.dispatch("raw_server_member_update", data)
            self.dispatch("server_member_update", old_member, member)
        self.dispatch("raw_server_member_update", data)

    def parse_serverroleupdate(self, data: ServerRoleUpdate) -> None:
        server = self.get_server(data["id"])
        if server is not None:
            old_server = copy.copy(server)
            server._from_data(data)
            self.dispatch("server_update", old_server, server)
        else:
            logger.debug(
                "SERVER_UPDATE referencing an unknown guild ID: %s. Discarding.",
                data["id"],
            )

    def parse_serverroledelete(self, data: ServerRoleDelete) -> None:
        self.dispatch("server_role_delete", data)

    def parse_userupdate(self, data: UserUpdate) -> None:
        user = self.get_user(data["id"])
        if user is not None:
            old_user = copy.copy(user)
            user._update(data)
            self.dispatch("raw_user_update", data)
            self.dispatch("user_update", old_user, user)
        self.dispatch("raw_user_update", data)

    def parse_userrelationship(self, data: UserRelationship) -> None:
        self.dispatch("user_relationship", data)

    # creaters

    def create_message(
        self,
        channel: MessageableChannel,
        data,
    ) -> Message:
        """Creates a :class:`~defectio.Message` from the given parameters.

        Parameters
        ----------
        channel : MessageableChannel
            The channel to create the message in.
        data : [type]
            A list of parameters required to create a message.

        Returns
        -------
        Message
            The message created.
        """
        return Message(state=self, channel=channel, data=data)

    def create_user(self, data: UserPayload) -> User:
        """Creates a :class:`~defectio.User` from the given parameters.

        Parameters
        ----------
        data : UserPayload
            A list of parameters required to create a user.

        Returns
        -------
        User
            The user created.
        """
        user = User(data, self)
        return user
