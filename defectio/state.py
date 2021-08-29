from __future__ import annotations

from revolt.server import Server
from typing import Dict, List, Deque, Optional, TYPE_CHECKING, Any, Callable, Union
from collections import deque
import asyncio
import inspect
from .message import Message
from .channel import Channel, channel_factory
from .user import User
from . import utils
import copy
from .raw_models import RawMessageDeleteEvent, RawMessageUpdateEvent

if TYPE_CHECKING:
    from .payloads import (
        Channel as ChannelPayload,
        Server as ServerPayload,
        User as UserPayload,
        MessageEventPayload,
        ReadyPayload,
    )
    from .http import HttpClient
    from .channel import TextChannel


class ConnectionState:
    if TYPE_CHECKING:
        _parsers: Dict[str, Callable[[Dict[str, Any]], None]]

    def __init__(
        self,
        dispatch: Callable,
        handlers: Dict[str, Callable],
        http: HttpClient,
        loop: asyncio.AbstractEventLoop,
        **options: Any,
    ):
        self.handlers: Dict[str, Callable] = handlers
        self.dispatch: Callable = dispatch
        self.http: HttpClient = http
        self.max_messages: Optional[int] = options.get("max_messages", 1000)
        self.loop: asyncio.AbstractEventLoop = loop
        self.servers: Dict[str, Server] = {}
        self.channels: Dict[str, Channel] = {}
        self.users: Dict[str, User] = {}
        self.user: Optional[User] = None

        self._messages: Optional[List[Message]] = deque(maxlen=self.max_messages)

        self.parsers = parsers = {}
        for attr, func in inspect.getmembers(self):
            if attr.startswith("parse_"):
                parsers[attr[6:]] = func

    def call_handlers(self, key: str, *args: Any, **kwargs: Any) -> None:
        try:
            func = self.handlers[key]
        except KeyError:
            pass
        else:
            func(*args, **kwargs)

    # Parsers

    def parse_authenticated(self, data):
        self.dispatch("authenticated")

    def parse_userupdate(self, data):
        self.dispatch("user_update")

    def parse_pong(self, data):
        self.dispatch("pong")

    def parse_ready(self, data: ReadyPayload) -> None:
        # if self._ready_task is not None:
        #     self._ready_task.cancel()

        for user in data["users"]:
            self.add_user(user)

        self.user = self.create_user(data=data["users"][0])

        for server in data["servers"]:
            self.add_server(server)

        for channel in data["channels"]:
            self.add_channel(channel)
        self.dispatch("ready")
        self.dispatch("connect")

    def parse_message(self, data: MessageEventPayload) -> None:
        channel = self.get_channel(data["channel"])
        print(channel)
        message = Message(channel=channel, data=data, state=self)
        self.dispatch("message", message)
        if self._messages is not None:
            self._messages.append(message)

    def parse_messageupdate(self, data):
        raw = RawMessageUpdateEvent(data)
        message = self._get_message(raw.message_id)
        if message is not None:
            older_message = copy.copy(message)
            raw.cached_message = older_message
            self.dispatch("raw_message_edit", raw)
            message._update(data)
            self.dispatch("message_edit", older_message, message)
        else:
            self.dispatch("raw_message_edit", raw)

    def parse_messagedelete(self, data):
        raw = RawMessageDeleteEvent(data)
        found = self._get_message(data["id"])
        raw.cached_message = found
        self.dispatch("raw_message_delete", raw)
        if self._messages is not None and found is not None:
            self.dispatch("message_delete", found)
            self._messages.remove(found)

    def parse_channelcreate(self, data):
        self.dispatch("channel_create")

    def parse_channelupdate(self, data):
        # self.add_channel(data)
        # self.users.get(data["id"]).online = True
        self.dispatch("channel_update")

    def parse_channeldelete(self, data):
        self.dispatch("channel_delete")

    def parse_channelgroupjoin(self, data):
        self.dispatch("channel_group_join")

    def parse_channelgroupleave(self, data):
        self.dispatch("channel_group_leave")

    def parse_channelstarttyping(self, data):
        self.dispatch("channel_start_typing")

    def parse_channelstoptyping(self, data):
        self.dispatch("channel_stop_typing")

    def parse_channelack(self, data):
        self.dispatch("channel_ack")

    def parse_serverupdate(self, data):
        # self.add_server(data)
        self.dispatch("server_update")

    def parse_serverdelete(self, data):
        self.dispatch("server_delete")

    def parse_servermemberjoin(self, data):
        self.dispatch("server_member_join")

    def parse_servermemberleave(self, data):
        self.dispatch("server_member_leave")

    def parse_servermemberupdate(self, data):
        self.dispatch("server_member_update")

    def parse_serverroleupdate(self, data):
        self.dispatch("server_role_update")

    def parse_serverroledelete(self, data):
        self.dispatch("server_role_delete")

    def parse_userupdate(self, data):
        # self.add_user(data)
        self.dispatch("user_update")

    def parse_userrelationship(self, data):
        self.dispatch("user_relationship")

    # Getters

    def get_user(self, id: str) -> Optional[User]:
        return self.users.get(id)

    def get_channel(self, id: str) -> Optional[Channel]:
        return self.channels.get(id)

    def get_server(self, id: str) -> Optional[Server]:
        return self.channels.get(id)

    def _get_message(self, msg_id: str) -> Optional[Message]:
        return (
            utils.find(lambda m: m.id == msg_id, reversed(self._messages))
            if self._messages
            else None
        )

    # Setters

    def add_user(self, payload: UserPayload) -> User:
        user = self.create_user(data=payload)
        self.users[user.id] = user
        return user

    def add_channel(self, payload: ChannelPayload) -> Channel:
        cls = channel_factory(payload)
        server = self.get_server(payload["server"])
        channel = cls(state=self, data=payload, server=server)
        self.channels[channel.id] = channel
        return channel

    def add_server(self, payload: ServerPayload) -> Server:
        server = Server(payload, self)
        self.servers[server.id] = server
        return server

    # creaters

    def create_message(
        self,
        *,
        channel: Union[TextChannel],
        data,
    ) -> Message:
        return Message(state=self, channel=channel, data=data)

    def create_user(self, *, data: UserPayload) -> User:
        user = User(data, self)
        return user
