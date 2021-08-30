from __future__ import annotations

from typing import TYPE_CHECKING, Optional
from .mixins import Hashable

if TYPE_CHECKING:
    from ..state import ConnectionState
    from ..types.payloads import User as UserPayload


class User(Hashable):
    def __init__(self, data: UserPayload, state: ConnectionState):
        self.state = state
        self.id = data["_id"]
        self.name = data["username"]
        self.owner: Optional[str]
        self.bot: bool

        bot = data.get("bot")
        if bot:
            self.bot = True
            self.owner = bot["owner"]
        else:
            self.bot = False
            self.owner = None

        self.badges = data.get("badges", 0)
        self.online = data.get("online", False)
        self.flags = data.get("flags", 0)
