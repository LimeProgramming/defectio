from __future__ import annotations

from typing import TYPE_CHECKING

from . import abc
from .mixins import Hashable

if TYPE_CHECKING:
    from ..state import ConnectionState
    from ..types.payloads import MemberPayload


class PartialMember(abc.Messageable, Hashable):
    def __init__(self, id: str, state: ConnectionState):
        self._state = state
        self.id = id

    def __repr__(self) -> str:
        return f"<PartialMember {self.id}>"

    def __str__(self) -> str:
        return self.id


class Member(PartialMember):
    def __init__(self, data: MemberPayload, state: ConnectionState):
        self._state = state
        self.nickname = data.get("nickname")
        self.id = data.get("_id").get("user")

    def __repr__(self) -> str:
        return f"<Member id={self.id} nickname={self.nickname}>"

    def __str__(self) -> str:
        return self.nickname
