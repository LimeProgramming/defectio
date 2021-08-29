from __future__ import annotations

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from .state import ConnectionState
    from .payloads import MessageEventPayload
    from .channel import Channel


class Message:
    def __init__(
        self, state: ConnectionState, channel: Channel, data: MessageEventPayload
    ):
        self._state: ConnectionState = state
        self.id: str = data["_id"]
        self.channel: Channel = channel
        self.content: str = data["content"]
        self.nonce: str = data["nonce"]
        self.author: str = data["author"]
