from __future__ import annotations

from typing import TYPE_CHECKING, Dict, List
from .mixins import Hashable

if TYPE_CHECKING:
    from ..types.payloads import Server as ServerPayload, Channel
    from ..state import ConnectionState
    from ..types.websocket import ServerUpdate
    from .member import Member


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
        self.categories = server.get("categories")
        self.roles = server.get("roles")
        self.icon = server.get("icon")
        self.banner = server.get("banner")
        self.default_permissions = server.get("default_permissions")
        self.system_message = server.get("system_message")

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
        return [self._state.get_channel(channel_id) for channel_id in self.channel_ids]

    @property
    def members(self) -> List[Member]:
        return self._state.get_members(self.id)
