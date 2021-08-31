from __future__ import annotations

import asyncio
import copy
import inspect
import logging
from collections import deque
from typing import Any
from typing import Callable
from typing import Deque
from typing import Dict
from typing import List
from typing import Optional
from typing import TYPE_CHECKING
from typing import Union

from defectio.gateway import DefectioWebsocket
from defectio.http import DefectioHTTP
from defectio.models.member import PartialMember

from . import utils
from .models import channel_factory
from .models import Member
from .models import Message
from .models import MessageableChannel
from .models import Server
from .models import User
from .models import VoiceChannel
from .models.raw_models import RawMessageDeleteEvent
from .models.raw_models import RawMessageUpdateEvent

if TYPE_CHECKING:
    from . import abc
    from .types.websocket import (
        Authenticated,
        ChannelAck,
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

logger = logging.getLogger("defectio")


class ConnectionState:
    def __init__(
        self,
        dispatch: Callable,
        handlers: Dict[str, Callable],
        http: Callable[..., DefectioHTTP],
        websocket: Callable[..., DefectioWebsocket],
        loop: asyncio.AbstractEventLoop,
        **options: Any,
    ):
        self.get_http = http
        self.get_websocket = websocket
        self.handlers: Dict[str, Callable] = handlers
        self.dispatch: Callable = dispatch
        self.max_messages: Optional[int] = options.get("max_messages", 1000)
        self.loop: asyncio.AbstractEventLoop = loop
        self.servers: Dict[str, Server] = {}
        self.channels: Dict[str, MessageableChannel] = {}
        self.users: Dict[str, User] = {}
        self.members: Dict[str, List[Union[Member | PartialMember]]] = {}
        self.user: Optional[User] = None

        self._messages: Optional[List[Message]] = deque(maxlen=self.max_messages)
        self.api_info: Optional[ApiInfoPayload] = None

        self.parsers: Dict[str, Callable[[Dict[str, Any]], None]] = {}
        for attr, func in inspect.getmembers(self):
            if attr.startswith("parse_"):
                self.parsers[attr[6:]] = func

    @property
    def http(self) -> DefectioHTTP:
        """Get http client.

        Returns
        -------
        DefectioHTTP
            HTTP client.
        """
        return self.get_http()

    @property
    def websocket(self) -> DefectioWebsocket:
        return self.get_websocket()

    def call_handlers(self, key: str, *args: Any, **kwargs: Any) -> None:
        try:
            func = self.handlers[key]
        except KeyError:
            pass
        else:
            func(*args, **kwargs)

    def set_api_info(self, api_info: ApiInfoPayload):
        self.api_info = api_info

    # Parsers

    def parse_authenticated(self, data: Authenticated):
        self.dispatch("authenticated", data)

    def parse_pong(self, data: Pong):
        self.dispatch("pong", data)

    def parse_ready(self, data: Ready) -> None:
        for user in data["users"]:
            self.add_user(user)

        self.user = self.create_user(data=data["users"][0])

        for server in data["servers"]:
            self.add_server(server)

        for channel in data["channels"]:
            self.add_channel(channel)

        for member in data["members"]:
            self.add_member(member["_id"])

        self.call_handlers("ready")
        self.dispatch("ready")
        self.dispatch("connect")

    def parse_message(self, data: MessagePayload) -> None:
        channel = self.get_channel(data["channel"])
        message = Message(channel=channel, data=data, state=self)
        self.dispatch("message", message)
        if self._messages is not None:
            self._messages.append(message)

    def parse_messageupdate(self, data: MessageUpdate):
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

    def parse_messagedelete(self, data: MessageDelete):
        raw = RawMessageDeleteEvent(data)
        found = self.get_message(data["id"])
        raw.cached_message = found
        self.dispatch("raw_message_delete", raw)
        if self._messages is not None and found is not None:
            self.dispatch("message_delete", found)
            self._messages.remove(found)

    def parse_channelcreate(self, data: ChannelCreate):
        channel = self.add_channel(data)
        self.dispatch("channel_create", channel)

    def parse_channelupdate(self, data: ChannelUpdate):
        self.dispatch("channel_update", data)

    def parse_channeldelete(self, data: ChannelDelete):
        channel = self.get_channel(data["id"])
        self.channels.pop(channel.id)
        self.dispatch("channel_delete", channel)

    def parse_channelgroupjoin(self, data: ChannelGroupJoin):
        self.dispatch("channel_group_join", data)

    def parse_channelgroupleave(self, data: ChannelGroupLeave):
        self.dispatch("channel_group_leave", data)

    def parse_channelstarttyping(self, data: ChannelStartTyping):
        self.dispatch("channel_start_typing", data)

    def parse_channelstoptyping(self, data: ChannelStopTyping):
        self.dispatch("channel_stop_typing", data)

    def parse_channelack(self, data: ChannelAck):
        self.dispatch("channel_ack", data)

    def parse_serverupdate(self, data: ServerUpdate):
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

    def parse_serverdelete(self, data: ServerDelete):
        server = self.get_server(data["id"])
        if server is not None:
            self.servers.pop(server.id)
        self.dispatch("server_delete", server)

    def parse_servermemberjoin(self, data: ServerMemberJoin):
        member = self.add_member(data)
        self.dispatch("server_member_join", member)

    def parse_servermemberleave(self, data: ServerMemberLeave):
        member = self.get_member(data["id"])
        self.members.get(data.get("id"), {}).pop(data.get("user"))
        self.dispatch("server_member_leave", member)

    def parse_servermemberupdate(self, data: ServerMemberUpdate):
        member = self.get_member(data["id"])
        if isinstance(member, Member):
            old_member = copy.copy(member)
            member._update(data)
            self.dispatch("raw_server_member_update", data)
            self.dispatch("server_member_update", old_member, member)
        self.dispatch("raw_server_member_update", data)

    def parse_serverroleupdate(self, data: ServerRoleUpdate):
        self.dispatch("server_role_update", data)

    def parse_serverroledelete(self, data: ServerRoleDelete):
        self.dispatch("server_role_delete", data)

    def parse_userupdate(self, data: UserUpdate):
        user = self.get_user(data["id"])
        if user is not None:
            old_user = copy.copy(user)
            user._update(data)
            self.dispatch("raw_user_update", data)
            self.dispatch("user_update", old_user, user)
        self.dispatch("raw_user_update", data)

    def parse_userrelationship(self, data: UserRelationship):
        self.dispatch("user_relationship", data)

    # Getters

    def get_user(self, id: str) -> Optional[User]:
        return self.users.get(id)

    def get_channel(self, id: str) -> Optional[Union[MessageableChannel, VoiceChannel]]:
        return self.channels.get(id)

    def get_server(self, id: str) -> Optional[Server]:
        return self.servers.get(id)

    def get_message(self, msg_id: str) -> Optional[Message]:
        return (
            utils.find(lambda m: m.id == msg_id, reversed(self._messages))
            if self._messages
            else None
        )

    def get_members(self, server_id: str) -> Optional[List[Member]]:
        return self.members.get(server_id)

    def get_member(self, server_id: str, user_id: str) -> Optional[Member]:
        return self.members.get(server_id, {}).get(user_id)

    # Setters

    def add_user(self, payload: UserPayload) -> User:
        user = self.create_user(data=payload)
        self.users[user.id] = user
        return user

    def add_channel(
        self, payload: ChannelPayload
    ) -> Union[MessageableChannel, VoiceChannel]:
        cls = channel_factory(payload)
        server = self.get_server(payload["server"])
        channel = cls(state=self, data=payload, server=server)
        self.channels[channel.id] = channel
        return channel

    def add_server(self, payload: ServerPayload) -> Server:
        server = Server(payload, self)
        self.servers[server.id] = server
        return server

    def add_member(self, payload: Union[MemberPayload | BasicMemberPayload]) -> Member:
        server = self.get_server(payload["server"])
        if "user" in payload:
            member = PartialMember(payload["user"], server, self)
        else:
            member = Member(payload, server, self)
        if server.id not in self.members:
            self.members[server.id] = {}
        self.members[server.id][member.id] = member
        return member

    # creaters

    def create_message(
        self,
        *,
        channel: MessageableChannel,
        data,
    ) -> Message:
        return Message(state=self, channel=channel, data=data)

    def create_user(self, *, data: UserPayload) -> User:
        user = User(data, self)
        return user
