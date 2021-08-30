from __future__ import annotations

from typing import Dict
from typing import List
from typing import TYPE_CHECKING

from .mixins import Hashable

if TYPE_CHECKING:
    from ..types.payloads import (
        Server as ServerPayload,
        CategoryPayload,
        SystemMessagePayload,
    )
    from ..state import ConnectionState
    from ..types.websocket import ServerUpdate
    from .member import Member
    from .channel import MessageableChannel


class SystemMessages:
    def __init__(
        self, data: SystemMessagePayload, server: Server, state: ConnectionState
    ) -> None:
        self._state = state
        self.server = server
        self.user_joined = state.get_channel(data.get("user_joined"))
        self.user_left = state.get_channel(data.get("user_left"))
        self.user_kicked = state.get_channel(data.get("user_kicked"))
        self.user_banned = state.get_channel(data.get("user_banned"))

    def __repr__(self) -> str:
        return (
            f"<SystemMessages server={self.server.id} "
            f"user_joined={self.user_joined} "
            f"user_left={self.user_left} "
            f"user_kicked={self.user_kicked} "
            f"user_banned={self.user_banned}>"
        )

    def __str__(self) -> str:
        return self.__repr__()


class Category(Hashable):
    def __init__(self, data: CategoryPayload, state: ConnectionState) -> None:
        self._state = state
        self.channels: List[MessageableChannel] = []
        self._from_data(data)

    def _from_data(self, data: CategoryPayload) -> None:
        self.id = data.get("id")
        self.title = data.get("title")
        for channel in data.get("channels", []):
            self.channels.append(self._state.get_channel(channel))


class Server(Hashable):
    def __init__(self, data: ServerPayload, state: ConnectionState):
        self.channel_ids: List[str] = []
        self.member_ids: List[str] = []
        self.categories: List[str] = []
        self._state: ConnectionState = state
        self._from_data(data)

    def _from_data(self, server: ServerPayload) -> None:
        self.id = server.get("_id")
        self.owner = server.get("owner")
        self.name = server.get("name")
        self.description = server.get("description")
        self.channel_ids = server.get("channels")
        self.member_ids = server.get("members")
        for category in server.get("categories", []):
            self.add_category(category)
        self.roles = server.get("roles")
        self.icon = server.get("icon")
        self.banner = server.get("banner")
        self.default_permissions = server.get("default_permissions")
        self.system_message = SystemMessages(  # weird ordering since servers are loaded before channels so on caching default to None # TODO
            server.get("system_messages"), self, self._state
        )

    def add_category(self, payload: CategoryPayload) -> None:
        category = Category(payload, self._state)
        self.categories.append(category)

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        attrs = (
            ("id", self.id),
            ("name", self.name),
            ("description", self.description or ""),
        )
        inner = " ".join("%s=%r" % t for t in attrs)
        return f"<Server {inner}>"

    def _update(self, payload: ServerUpdate):
        for k, v in payload.items():
            setattr(self, k, v)

    @property
    def channels(self):
        """All channels in the server

        Returns
        -------
        [type]
            List of all channels
        """
        return [self._state.get_channel(channel_id) for channel_id in self.channel_ids]

    @property
    def members(self) -> List[Member]:
        """All cached members in the server.

        Returns
        -------
        List[Member]
            List of all cached members in the server.
        """
        return self._state.get_members(self.id)
