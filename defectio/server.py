from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .payloads import Server as ServerPayload
    from .state import ConnectionState


class Server:
    def __init__(self, data: ServerPayload, state: ConnectionState):
        self.state = state
        self.id = data["_id"]
