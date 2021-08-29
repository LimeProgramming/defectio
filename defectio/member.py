from __future__ import annotations

from . import abc


from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .state import ConnectionState
    from .server import Server


class Member(abc.Messageable):
    def __init__(self, id: str, server: Server, state: ConnectionState):
        self._state = state
        self.server = server
        self.id = id
