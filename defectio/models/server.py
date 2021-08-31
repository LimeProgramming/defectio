from __future__ import annotations

from typing import Dict, Optional
from typing import List
from typing import TYPE_CHECKING

from .mixins import Hashable

if TYPE_CHECKING:
    from ..types.payloads import (
        ServerPayload,
        CategoryPayload,
        SystemMessagePayload,
        RolePayload,
    )
    from ..state import ConnectionState
    from ..types.websocket import ServerUpdate, ServerRoleUpdate
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


class Role(Hashable):
    def __init__(self, id: str, data: RolePayload, state: ConnectionState) -> None:
        self.id = id
        self._state = state
        self.name = data.get("name")
        self.colour = data.get("colour")
        self.hoist = data.get("hoist", False)
        self.rank = data.get("rank")

    def _update(self, event: ServerRoleUpdate) -> None:
        if event.get("clear") == "Colour":
            self.colour = None
        self.name = event.get("name", self.name)
        self.hoist = event.get("hoist", self.hoist)
        self.rank = event.get("rank", self.rank)

    def __str__(self) -> str:
        return self.__repr__()

    def __repr__(self) -> str:
        return f"<Role server={self.server.id} name={self.name}>"


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

    def _from_data(self, data: ServerPayload) -> None:
        self.id = data.get("_id")
        self.owner = data.get("owner")
        self.name = data.get("name")
        self.description = data.get("description")
        self.channel_ids = data.get("channels")
        self.member_ids = data.get("members")
        self.categories = [
            Category(payload, self._state) for payload in data.get("categories", [])
        ]
        self.roles: List[Role] = []
        for key, value in data.get("roles", {}).items():
            self.roles.append(Role(key, value, self._state))
        self.icon = data.get("icon")
        self.banner = data.get("banner")
        self.default_permissions = data.get("default_permissions")
        self.system_message = SystemMessages(  # weird ordering since servers are loaded before channels so on caching default to None # TODO
            data.get("system_messages"), self, self._state
        )

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

    def create_text_channel(
        self, name: str, *, description: Optional[str] = None
    ) -> MessageableChannel:
        channel = self._state.http.create_channel(self.id, name, "Text", description)
        self._state.add_channel(channel)
        self.channel_ids.append(channel["_id"])

    def create_voice_channel(self, name: str):
        channel = self._state.http.create_channel(self.id, name, "Voice")
        self._state.add_channel(channel)
        self.channel_ids.append(channel["_id"])

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
