from typing import List
from typing import Literal
from typing import Optional
from typing import TypedDict

from .payloads import Channel
from .payloads import Member
from .payloads import Message as MessagePayload
from .payloads import RelationType
from .payloads import Role
from .payloads import Server
from .payloads import User


class Error(TypedDict):
    type: str
    error: str


class Authenticated(TypedDict):
    type: Literal["Authenticated"]


class Pong(TypedDict):
    type: Literal["Pong"]
    time: int


class Ready(TypedDict):
    type: Literal["Ready"]
    users: List[User]
    servers: List[Server]
    channels: List[Channel]


class Message(MessagePayload):
    type: Literal["Message"]


class PartialMessage(MessagePayload, total=False):
    pass


class MessageUpdate(TypedDict):
    type: Literal["MessageUpdate"]
    id: str
    data: PartialMessage


class MessageDelete(TypedDict):
    type: Literal["MessageDelete"]
    id: str
    channel: str


class ChannelCreate(Channel):
    type: Literal["ChannelCreate"]


class PartialChannel(Channel, total=False):
    pass


class ChannelUpdate(TypedDict):
    type: Literal["ChannelUpdate"]
    id: str
    data: PartialChannel
    clear: Optional[Literal["Icon", "Description"]]


class ChannelDelete(TypedDict):
    type: Literal["ChannelDelete"]
    id: str


class ChannelGroupJoin(TypedDict):
    type: Literal["ChannelGroupJoin"]
    id: str
    user: str


class ChannelGroupLeave(TypedDict):
    type: Literal["ChannelGroupLeave"]
    id: str
    user: str


class ChannelStartTyping(TypedDict):
    type: Literal["ChannelStartTyping"]
    id: str
    user: str


class ChannelStopTyping(TypedDict):
    type: Literal["ChannelStopTyping"]
    id: str
    user: str


class ChannelAck(TypedDict):
    type: Literal["ChannelAck"]
    id: str
    user: str
    message_id: str


class PartialServer(Server, total=False):
    pass


class ServerUpdate(TypedDict):
    type: Literal["ServerUpdate"]
    id: str
    data: PartialServer
    clear: Optional[Literal["Icon", "Description", "Bannerss"]]


class ServerDelete(TypedDict):
    type: Literal["ServerDelete"]
    id: str


class PartialServerMember(Member, total=False):
    pass


class ServerMemberUpdate(TypedDict):
    type: Literal["ServerMemberUpdate"]
    id: str
    data: PartialServerMember
    clear: Optional[Literal["Nickname", "Avatar"]]


class ServerMemberJoin(TypedDict):
    type: Literal["ServerMemberJoin"]
    id: str
    user: str


class ServerMemberLeave(TypedDict):
    type: Literal["ServerMemberLeave"]
    id: str
    user: str


class PartialServerRole(Role, total=False):
    pass


class ServerRoleUpdate(TypedDict):
    type: Literal["ServerRoleUpdate"]
    id: str
    data: PartialServerRole
    clear: Optional[Literal["Colour"]]


class ServerRoleDelete(TypedDict):
    type: Literal["ServerRoleDelete"]
    id: str
    role_id: str


class PartialUser(User, total=False):
    pass


class UserUpdate(TypedDict):
    type: Literal["UserUpdate"]
    id: str
    data: PartialUser
    clear: Optional[
        Literal["ProfileContent", "ProfileBackground", "StatusText", "Avatar"]
    ]


class UserRelationship(TypedDict):
    type: Literal["UserRelationship"]
    id: str
    user: str
    type: RelationType
