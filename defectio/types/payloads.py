from typing import Any
from typing import Dict
from typing import List
from typing import Literal
from typing import Optional
from typing import Tuple
from typing import Type
from typing import TypedDict

RelationType = Literal[
    "Blocked", "BlockedOther", "Friend", "Incoming", "None", "Outgoing", "User"
]
ChannelType = Literal[
    "SavedMessage", "DirectMessage", "Group", "TextChannel", "VoiceChannel"
]


class ApiInfoFeaturePayload(TypedDict):
    registration: bool
    captcha: Dict[str, Any]
    email: bool
    invite_only: str
    autumn: Dict[str, Any]
    january: Dict[str, Any]
    voso: Dict[str, Any]


class ApiInfoPayload(TypedDict):
    revolt: str
    features: ApiInfoFeaturePayload
    ws: str
    app: str
    vapid: str


class LoginPayload(TypedDict):
    id: str
    user_id: str
    session_token: str


class SessionPayload(TypedDict):
    id: str
    friendly_name: str


class MetadataPayload(TypedDict):
    type: Literal["File", "Text", "Audio", "Image", "Video"]


class RelationshipPayload(TypedDict):
    status: RelationType
    _id: str


class StatusPayload(TypedDict):
    text: str
    presence: Literal["Busy", "Idle", "Invisible", "Online", "Offline"]


class UserBotInfoPayload(TypedDict):
    owner: str


class AttachmentPayload(TypedDict):
    _id: str
    tag: Literal["attachments"]
    size: int
    filename: str
    metadata: MetadataPayload
    content_type: str


class UserPayload(TypedDict):
    _id: str
    username: str
    avatar: AttachmentPayload
    relations: List[RelationshipPayload]
    badges: int
    status: StatusPayload
    relationship: RelationType
    online: bool
    flags: int
    bot: UserBotInfoPayload


class ProfilePayload(TypedDict):
    content: str
    background: AttachmentPayload


MutualFriends = TypedDict("MutualFriends", {"users": List[str]})


class LastMessagePayload(TypedDict):
    _id: str
    author: str
    short: str


class DMChannelPayload(TypedDict):
    _id: str
    channel_type: Literal["DirectMessage"]
    active: bool
    recipients: List[str]
    last_message: LastMessagePayload


class RelationshipStatusPayload(TypedDict):
    status: RelationType


class IconPayload(TypedDict):
    _id: str
    tag: str
    size: int
    filename: str
    content_type: str
    metadata: MetadataPayload


class ChannelPayload(TypedDict):
    _id: str
    server: str
    name: str
    description: str
    icon: IconPayload
    default_permissions: int
    role_permissions: Dict[str, int]
    channel_type: ChannelType


class EditChannelPayload(TypedDict):
    name: str
    description: str
    icon: str
    remove: Literal["Description", "Icon"]


ChannelInvite = TypedDict("ChannelInvite", {"code": str})


class ContentPayload(TypedDict):
    type: str
    content: str


Edited = TypedDict("Edited", {"con$datatent": str})

Embed = TypedDict("Embed", {"type": str})


class MessagePayload(TypedDict):
    _id: str
    nonce: Optional[str]
    channel: str
    author: str
    content: ContentPayload
    attachments: List[AttachmentPayload]
    edited: Edited
    embeds: List[Embed]
    mentions: List[str]
    replies: List[str]


class MemberIdPayload(TypedDict):
    server: str
    user: str


class BasicMemberPayload(TypedDict):
    _id: str
    nickname: str


class FetchMessagePayload(TypedDict):
    messages: List[MessagePayload]
    users: List[UserPayload]
    members: List[BasicMemberPayload]
    avatar: AttachmentPayload
    roles: List[str]


class MessagePollPayload(TypedDict):
    changed: List[MessagePayload]
    deleted: List[str]


class SearchMessagePayload(TypedDict):
    messages: List[MessagePayload]
    users: List[UserPayload]
    members: List[BasicMemberPayload]


class GroupPayload(TypedDict):
    _id: str
    channel_type: Literal["Group"]
    recipients: List[str]
    name: str
    owner: str
    description: str
    last_message: LastMessagePayload
    icon: IconPayload
    permissions: int


JoinCall = TypedDict("JoinCall", {"token": str})


class CategoryPayload(TypedDict):
    id: str
    title: str
    channels: List[str]


class SystemMessagePayload(TypedDict):
    user_joined: str
    user_left: str
    user_kicked: str
    user_banned: str


class RolePayload(TypedDict):
    name: str
    colour: str
    hoist: Optional[bool]
    rank: int
    permissions: List[int]


class BannerPayload(TypedDict):
    _id: str
    tag: Literal["attachments"]
    size: int
    filename: str
    content_type: str
    metadata: MetadataPayload


class ServerPayload(TypedDict):
    _id: str
    nonce: Optional[str]
    owner: str
    name: str
    description: Optional[str]
    channels: List[str]
    categories: List[CategoryPayload]
    system_message: SystemMessagePayload
    roles: Dict[str, RolePayload]
    default_permissions: List[int]
    icon: IconPayload
    banner: BannerPayload


class ChannelPayload(TypedDict):
    type: ChannelType
    name: str
    description: str
    nonce: Optional[str]


class MemberPayload(TypedDict):
    _id: MemberIdPayload
    nickname: str
    avatar: AttachmentPayload
    roles: List[str]


class ServerMembersPayload(TypedDict):
    members: List[MemberPayload]
    users: List[UserPayload]


class BanPayload(TypedDict):
    _id: MemberIdPayload
    reason: str


class BansPayload(TypedDict):
    users: List[UserPayload]
    bans: List[BanPayload]


class CreateRole(Type):
    id: str
    permissions: List[int]


class BotPayload(TypedDict):
    _id: str
    owner: str
    token: str
    public: bool
    interactiosURL: str


class PublicBotPayload(TypedDict):
    _id: str
    username: str
    avatar: AttachmentPayload
    description: str


class InvitePayload(TypedDict):
    type: Literal["Server"]
    server_id: str
    server_name: str
    server_icon: AttachmentPayload
    server_banner: BannerPayload
    channel_id: str
    channel_name: str
    channel_description: str
    user_avatar: AttachmentPayload
    member_count: int


class InviteChannelPayload(TypedDict):
    _id: str
    channel_type: Literal["SavedMessages"]
    user: str
    nonce: str


class JoinInvitePayload(TypedDict):
    type: Literal["Server"]
    channel: InviteChannelPayload
    server: ServerPayload


Settings = Dict[str, Tuple[int, str]]


class UnreadsPayload(TypedDict):
    _id: MemberIdPayload
    last_id: str
    mentions: List[str]
