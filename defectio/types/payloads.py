from typing import Literal, Tuple, Type, Dict, List, Any, TypedDict, Optional

RelationType = Literal[
    "Blocked", "BlockedOther", "Friend", "Incoming", "None", "Outgoing", "User"
]
ChannelType = Literal[
    "SavedMessage", "DirectMessage", "Group", "TextChannel", "VoiceChannel"
]


class ApiInfoFeature(TypedDict):
    registration: bool
    captcha: Dict[str, Any]
    email: bool
    invite_only: str
    autumn: Dict[str, Any]
    january: Dict[str, Any]
    voso: Dict[str, Any]


class ApiInfo(TypedDict):
    revolt: str
    features: ApiInfoFeature
    ws: str
    app: str
    vapid: str


class Login(TypedDict):
    id: str
    user_id: str
    session_token: str


class Session(TypedDict):
    id: str
    friendly_name: str


class Metadata(TypedDict):
    type: Literal["File", "Text", "Audio", "Image", "Video"]


class Relationship(TypedDict):
    status: RelationType
    _id: str


class Status(TypedDict):
    text: str
    presence: RelationType


class UserBotInfo(TypedDict):
    owner: str


class Attachment(TypedDict):
    _id: str
    tag: Literal["attachments"]
    size: 0
    filename: str
    metadata: Metadata
    content_type: str


class User(TypedDict):
    _id: str
    username: str
    avatar: Attachment
    relations: List[Relationship]
    badges: int
    status: Status
    relationship: RelationType
    online: bool
    flags: int
    bot: UserBotInfo


class Profile(TypedDict):
    content: str
    background: Attachment


MutualFriends = TypedDict("MutualFriends", {"users": List[str]})


class LastMessage(TypedDict):
    _id: str
    author: str
    short: str


class DMChannel(TypedDict):
    _id: str
    channel_type: Literal["DirectMessage"]
    active: bool
    recipients: List[str]
    last_message: LastMessage


class RelationshipStatus(TypedDict):
    status: RelationType


class Icon(TypedDict):
    _id: str
    tag: str
    size: int
    filename: str
    content_type: str
    metadata: Metadata


class Channel(TypedDict):
    _id: str
    server: str
    name: str
    description: str
    icon: Icon
    default_permissions: int
    role_permissions: Dict[str, int]
    channel_type: ChannelType


class EditChannel(TypedDict):
    name: str
    description: str
    icon: str
    remove: Literal["Description", "Icon"]


ChannelInvite = TypedDict("ChannelInvite", {"code": str})


class Content(TypedDict):
    type: str
    content: str


Edited = TypedDict("Edited", {"con$datatent": str})

Embed = TypedDict("Embed", {"type": str})


class Message(TypedDict):
    _id: str
    nonce: Optional[str]
    channel: str
    author: str
    content: Content
    attachments: List[Attachment]
    edited: Edited
    embeds: List[Embed]
    mentions: List[str]
    replies: List[str]


class MemberId(TypedDict):
    server: str
    user: str


class BasicMember(TypedDict):
    _id: str
    nickname: str


class FetchMessage(TypedDict):
    messages: List[Message]
    users: List[User]
    members: List[BasicMember]
    avatar: Attachment
    roles: List[str]


class MessagePoll(TypedDict):
    changed: List[Message]
    deleted: List[str]


class SearchMessage(TypedDict):
    messages: List[Message]
    users: List[User]
    members: List[BasicMember]


class Group(TypedDict):
    _id: str
    channel_type: Literal["Group"]
    recipients: List[str]
    name: str
    owner: str
    description: str
    last_message: LastMessage
    icon: Icon
    permissions: int


JoinCall = TypedDict("JoinCall", {"token": str})


class Category(TypedDict):
    id: str
    title: str
    channels: List[str]


class SystemMessage(TypedDict):
    user_joined: str
    user_left: str
    user_kicked: str
    user_banned: str


class Role(TypedDict):
    name: str
    colour: str
    hoist: bool
    rank: 0
    permissions: List[int]


class Banner(TypedDict):
    _id: str
    tag: Literal["attachments"]
    size: int
    filename: str
    content_type: str
    metadata: Metadata


class Server(TypedDict):
    _id: str
    nonce: Optional[str]
    owner: str
    name: str
    description: Optional[str]
    channels: List[str]
    categories: List[Category]
    system_message: SystemMessage
    roles: Dict[str, Role]
    default_permissions: List[int]
    icon: Icon
    banner: Banner


class Channel(TypedDict):
    type: ChannelType
    name: str
    description: str
    nonce: Optional[str]


class Member(TypedDict):
    _id: MemberId
    nickname: str
    avatar: Attachment
    roles: List[str]


class ServerMembers(TypedDict):
    members: List[Member]
    users: List[User]


class Ban(TypedDict):
    _id: MemberId
    reason: str


class Bans(TypedDict):
    users: List[User]
    bans: List[Ban]


class CreateRole(Type):
    id: str
    permissions: List[int]


class Bot(TypedDict):
    _id: str
    owner: str
    token: str
    public: bool
    interactiosURL: str


class PublicBot(TypedDict):
    _id: str
    username: str
    avatar: Attachment
    description: str


class Invite(TypedDict):
    type: Literal["Server"]
    server_id: str
    server_name: str
    server_icon: Attachment
    server_banner: Banner
    channel_id: str
    channel_name: str
    channel_description: str
    user_avatar: Attachment
    member_count: int


class InviteChannel(TypedDict):
    _id: str
    channel_type: Literal["SavedMessages"]
    user: str
    nonce: str


class JoinInvite(TypedDict):
    type: Literal["Server"]
    channel: InviteChannel
    server: Server


Settings = Dict[str : Tuple[int, str]]


class Unreads(TypedDict):
    _id: MemberId
    last_id: str
    mentions: List[str]
