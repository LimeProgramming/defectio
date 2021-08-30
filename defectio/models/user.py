from __future__ import annotations

from typing import Optional
from typing import TYPE_CHECKING

from .mixins import Hashable

if TYPE_CHECKING:
    from ..state import ConnectionState
    from ..types.payloads import User as UserPayload


class PartialUser(Hashable):
    def __init__(
        self,
        id: str,
    ) -> None:
        self.id = id

    def __repr__(self) -> str:
        return f"<PartialUser id={self.id!r}>"

    def __str__(self) -> str:
        return self.id


class User(PartialUser):
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

    def __repr__(self) -> str:
        return f"<User id={self.id!r} name={self.name!r}>"

    def __str__(self) -> str:
        return self.name
