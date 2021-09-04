from __future__ import annotations

from typing import Any
from typing import Callable
from typing import ClassVar
from typing import Iterator
from typing import Optional
from typing import Set
from typing import Type
from typing import TYPE_CHECKING
from typing import TypeVar

from .flags import alias_flag_value
from .flags import BaseFlags
from .flags import fill_with_flags
from .flags import flag_value

__all__ = ("ServerPermissions", "ChannelPermissions", "ChannelPermissionOverwrite")

# A permission alias works like a regular flag but is marked
# So the ChannelPermissionOverwrite knows to work with it
class permission_alias(alias_flag_value):
    alias: str


def make_permission_alias(
    alias: str,
) -> Callable[[Callable[[Any], int]], permission_alias]:
    def decorator(func: Callable[[Any], int]) -> permission_alias:
        ret = permission_alias(func)
        ret.alias = alias
        return ret

    return decorator


SP = TypeVar("SP", bound="ServerPermissions")
CP = TypeVar("CP", bound="ChannelPermissions")


def _augment_from_channelpermissions(cls):
    cls.VALID_NAMES = set(ChannelPermissions.VALID_FLAGS)
    aliases = set()

    # make descriptors for all the valid names and aliases
    for name, value in ChannelPermissions.__dict__.items():
        if isinstance(value, permission_alias):
            key = value.alias
            aliases.add(name)
        elif isinstance(value, flag_value):
            key = name
        else:
            continue

        # god bless Python
        def getter(self, x=key):
            return self._values.get(x)

        def setter(self, value, x=key):
            self._set(x, value)

        prop = property(getter, setter)
        setattr(cls, name, prop)

    cls.PURE_FLAGS = cls.VALID_NAMES - aliases
    return cls


@fill_with_flags()
class ServerPermissions(BaseFlags):
    def __init__(self, permissions: int = 0, **kwargs: bool):
        if not isinstance(permissions, int):
            raise TypeError(
                f"Expected int parameter, received {permissions.__class__.__name__} instead."
            )

        self.value = permissions
        for key, value in kwargs.items():
            if key not in self.VALID_FLAGS:
                raise TypeError(f"{key!r} is not a valid permission name.")
            setattr(self, key, value)

    # UF
    def is_subset(self, other: ServerPermissions) -> bool:
        """Returns ``True`` if self has the same or fewer permissions as other."""
        if isinstance(other, ServerPermissions):
            return (self.value & other.value) == self.value
        else:
            raise TypeError(
                f"cannot compare {self.__class__.__name__} with {other.__class__.__name__}"
            )

    # UF
    def is_superset(self, other: ServerPermissions) -> bool:
        """Returns ``True`` if self has the same or more permissions as other."""
        if isinstance(other, ServerPermissions):
            return (self.value | other.value) == self.value
        else:
            raise TypeError(
                f"cannot compare {self.__class__.__name__} with {other.__class__.__name__}"
            )

    # UF
    def is_strict_subset(self, other: ServerPermissions) -> bool:
        """Returns ``True`` if the permissions on other are a strict subset of those on self."""
        return self.is_subset(other) and self != other

    # UF
    def is_strict_superset(self, other: ServerPermissions) -> bool:
        """Returns ``True`` if the permissions on other are a strict superset of those on self."""
        return self.is_superset(other) and self != other

    __le__ = is_subset
    __ge__ = is_superset
    __lt__ = is_strict_subset
    __gt__ = is_strict_superset

    @classmethod
    def none(cls: Type[SP]) -> SP:
        """A factory method that creates a :class:`ServerPermissions` with all
        permissions set to ``False``."""
        return cls(0)

    @classmethod
    def all(cls: Type[SP]) -> SP:
        """A factory method that creates a :class:`ServerPermissions` with all
        permissions set to ``True``.
        """
        return cls(0b111111111111111111111111111111111111111)

    @flag_value
    def view(self) -> int:
        """:class:`bool`: Returns ``True`` if a user can... unknown."""
        return 1 << 0

    @flag_value
    def manage_roles(self) -> int:
        """:class:`bool`: Returns ``True`` if a user can create or edit roles less than their role's position."""
        return 1 << 1

    @flag_value
    def manage_channels(self) -> int:
        """:class:`bool`: Returns ``True`` if a user can edit, delete, or create channels in the server."""
        return 1 << 2

    @flag_value
    def manage_server(self) -> int:
        """:class:`bool`: Returns ``True`` if a user can edit server properties."""
        return 1 << 3

    @flag_value
    def kick_members(self) -> int:
        """:class:`bool`: Returns ``True`` if the user can kick users from the server."""
        return 1 << 4

    @flag_value
    def ban_members(self) -> int:
        """:class:`bool`: Returns ``True`` if a user can ban users from the server."""
        return 1 << 5

    @flag_value
    def change_nickname(self) -> int:
        """:class:`bool`: Returns ``True`` if a user can change their nickname in the server."""
        return 1 << 12

    @flag_value
    def manage_nicknames(self) -> int:
        """:class:`bool`: Returns ``True`` if a user can change other user's nickname in the server."""
        return 1 << 13

    @flag_value
    def change_avatar(self) -> int:
        """:class:`bool`: Returns ``True`` if a user can change their avatar in the server."""
        return 1 << 14

    @flag_value
    def remove_avatar(self) -> int:
        """:class:`bool`: Returns ``True`` if a users can remove the avatars of other users on the server."""
        return 1 << 15


@fill_with_flags()
class ChannelPermissions(BaseFlags):
    def __init__(self, permissions: int = 0, **kwargs: bool):
        if not isinstance(permissions, int):
            raise TypeError(
                f"Expected int parameter, received {permissions.__class__.__name__} instead."
            )

        self.value = permissions
        for key, value in kwargs.items():
            if key not in self.VALID_FLAGS:
                raise TypeError(f"{key!r} is not a valid permission name.")
            setattr(self, key, value)

    # UF
    def is_subset(self, other: ChannelPermissions) -> bool:
        """Returns ``True`` if self has the same or fewer permissions as other."""
        if isinstance(other, ChannelPermissions):
            return (self.value & other.value) == self.value
        else:
            raise TypeError(
                f"cannot compare {self.__class__.__name__} with {other.__class__.__name__}"
            )

    # UF
    def is_superset(self, other: ChannelPermissions) -> bool:
        """Returns ``True`` if self has the same or more permissions as other."""
        if isinstance(other, ChannelPermissions):
            return (self.value | other.value) == self.value
        else:
            raise TypeError(
                f"cannot compare {self.__class__.__name__} with {other.__class__.__name__}"
            )

    # UF
    def is_strict_subset(self, other: ChannelPermissions) -> bool:
        """Returns ``True`` if the permissions on other are a strict subset of those on self."""
        return self.is_subset(other) and self != other

    # UF
    def is_strict_superset(self, other: ChannelPermissions) -> bool:
        """Returns ``True`` if the permissions on other are a strict superset of those on self."""
        return self.is_superset(other) and self != other

    __le__ = is_subset
    __ge__ = is_superset
    __lt__ = is_strict_subset
    __gt__ = is_strict_superset

    @classmethod
    def none(cls: Type[CP]) -> CP:
        """A factory method that creates a :class:`ChannelPermissions` with all
        permissions set to ``False``."""
        return cls(0)

    @classmethod
    def all(cls: Type[CP]) -> CP:
        """A factory method that creates a :class:`ChannelPermissions` with all
        permissions set to ``True``.
        """
        return cls(0b111111111111111111111111111111111111111)

    def handle_overwrite(self, allow: int, deny: int) -> None:
        # Basically this is what's happening here.
        # We have an original bit array, e.g. 1010
        # Then we have another bit array that is 'denied', e.g. 1111
        # And then we have the last one which is 'allowed', e.g. 0101
        # We want original OP denied to end up resulting in
        # whatever is in denied to be set to 0.
        # So 1010 OP 1111 -> 0000
        # Then we take this value and look at the allowed values.
        # And whatever is allowed is set to 1.
        # So 0000 OP2 0101 -> 0101
        # The OP is base  & ~denied.
        # The OP2 is base | allowed.
        self.value = (self.value & ~deny) | allow

    @flag_value
    def view_channel(self) -> int:
        """:class:`bool`: Returns ``True`` if a user can view all or specific text channels.
        .. note::
            Note that there is currently no ways to edit this permission with Revolt UI.
        """
        return 1 << 0

    @make_permission_alias("view_channel")
    def read_messages(self) -> int:
        """:class:`bool`: An alias for :attr:`view_channel`."""
        return 1 << 0

    @flag_value
    def send_messages(self) -> int:
        """:class:`bool`: Returns ``True`` if a user can send messages from all or specific text channels."""
        return 1 << 1

    @flag_value
    def manage_messages(self) -> int:
        """:class:`bool`: Returns ``True`` if a user can delete or pin messages in a text channel.
        .. note::
            Note that there are currently no ways to edit other people's messages.
        """
        return 1 << 2

    @flag_value
    def manage_channel(self) -> int:
        """:class:`bool`: Returns ``True`` if a user can edit, delete, or create channels in the server."""
        return 1 << 3

    @flag_value
    def voice_call(self) -> int:
        """:class:`bool`: Returns ``True`` if a user can connect to a voice channel."""
        return 1 << 4

    @make_permission_alias("voice_call")
    def connect(self) -> int:
        """:class:`bool`: An alias for :attr:`voice_call`."""
        return 1 << 4

    @flag_value
    def invite_others(self) -> int:
        """:class:`bool`: Returns ``True`` if the user can invite others."""
        return 1 << 5

    @make_permission_alias("invite_others")
    def create_instant_invite(self) -> int:
        """:class:`bool`: An alias for :attr:`invite_others`."""
        return 1 << 5

    @flag_value
    def embed_links(self) -> int:
        """:class:`bool`: Returns ``True`` if a user's messages will automatically be embedded by Discord."""
        return 1 << 6

    @flag_value
    def upload_files(self) -> int:
        """:class:`bool`: Returns ``True`` if a user can send files in their messages."""
        return 1 << 7

    @make_permission_alias("upload_files")
    def attach_files(self) -> int:
        """:class:`bool`: An alias for :attr:`upload_files`."""
        return 1 << 7


PO = TypeVar("PO", bound="ChannelPermissionsOverwrite")


@_augment_from_channelpermissions
class ChannelPermissionsOverwrite:
    r"""A type that is used to represent a channel specific permission.
    Unlike a regular :class:`Permissions`\, the default value of a
    permission is equivalent to ``None`` and not ``False``. Setting
    a value to ``False`` is **explicitly** denying that permission,
    while setting a value to ``True`` is **explicitly** allowing
    that permission.
    The values supported by this are the same as :class:`Permissions`
    with the added possibility of it being set to ``None``.
    .. container:: operations
        .. describe:: x == y
            Checks if two overwrites are equal.
        .. describe:: x != y
            Checks if two overwrites are not equal.
        .. describe:: iter(x)
           Returns an iterator of ``(perm, value)`` pairs. This allows it
           to be, for example, constructed as a dict or a list of pairs.
           Note that aliases are not shown.
    Parameters
    -----------
    \*\*kwargs
        Set the value of permissions by their name.
    """

    __slots__ = ("_values",)

    if TYPE_CHECKING:
        VALID_NAMES: ClassVar[Set[str]]
        PURE_FLAGS: ClassVar[Set[str]]
        # I wish I didn't have to do this
        view_channel: Optional[bool]
        send_messages: Optional[bool]
        manage_messages: Optional[bool]
        manage_channels: Optional[bool]
        voice_call: Optional[bool]
        invite_others: Optional[bool]
        embed_links: Optional[bool]
        upload_files: Optional[bool]

    def __init__(self, **kwargs: Optional[bool]):
        self._values: dict[str, Optional[bool]] = {}

        for key, value in kwargs.items():
            if key not in self.VALID_NAMES:
                raise ValueError(f"no permission called {key}.")

            setattr(self, key, value)

    def __eq__(self, other: Any) -> bool:
        return (
            isinstance(other, ChannelPermissionsOverwrite)
            and self._values == other._values
        )

    def _set(self, key: str, value: Optional[bool]) -> None:
        if value not in (True, None, False):
            raise TypeError(
                f"Expected bool or NoneType, received {value.__class__.__name__}"
            )

        if value is None:
            self._values.pop(key, None)
        else:
            self._values[key] = value

    def pair(self) -> tuple[ChannelPermissions, ChannelPermissions]:
        """tuple[:class:`Permissions`, :class:`Permissions`]: Returns the (allow, deny) pair from this overwrite."""

        allow = ChannelPermissions.none()
        deny = ChannelPermissions.none()

        for key, value in self._values.items():
            if value is True:
                setattr(allow, key, True)
            elif value is False:
                setattr(deny, key, True)

        return allow, deny

    @classmethod
    def from_pair(
        cls: Type[PO], allow: ChannelPermissions, deny: ChannelPermissions
    ) -> PO:
        """Creates an overwrite from an allow/deny pair of :class:`Permissions`."""
        ret = cls()
        for key, value in allow:
            if value is True:
                setattr(ret, key, True)

        for key, value in deny:
            if value is True:
                setattr(ret, key, False)

        return ret

    def is_empty(self) -> bool:
        """Checks if the permission overwrite is currently empty.
        An empty permission overwrite is one that has no overwrites set
        to ``True`` or ``False``.
        Returns
        -------
        :class:`bool`
            Indicates if the overwrite is empty.
        """
        return len(self._values) == 0

    def update(self, **kwargs: bool) -> None:
        r"""Bulk updates this permission overwrite object.
        Allows you to set multiple attributes by using keyword
        arguments. The names must be equivalent to the properties
        listed. Extraneous key/value pairs will be silently ignored.
        Parameters
        ------------
        \*\*kwargs
            A list of key/value pairs to bulk update with.
        """
        for key, value in kwargs.items():
            if key not in self.VALID_NAMES:
                continue

            setattr(self, key, value)

    def __iter__(self) -> Iterator[tuple[str, Optional[bool]]]:
        for key in self.PURE_FLAGS:
            yield key, self._values.get(key)


"""
export const UserPermission = {
    Access: 0b00000000000000000000000000000001,      // 1
    ViewProfile: 0b00000000000000000000000000000010, // 2
    SendMessage: 0b00000000000000000000000000000100, // 4
    Invite: 0b00000000000000000000000000001000,      // 8
}

export const ChannelPermission = {
    View: 0b00000000000000000000000000000001,           // 1
    SendMessage: 0b00000000000000000000000000000010,    // 2
    ManageMessages: 0b00000000000000000000000000000100, // 4
    ManageChannel: 0b00000000000000000000000000001000,  // 8
    VoiceCall: 0b00000000000000000000000000010000,      // 16
    InviteOthers: 0b00000000000000000000000000100000,   // 32
    EmbedLinks: 0b00000000000000000000000001000000,   // 64
    UploadFiles: 0b00000000000000000000000010000000,   // 128
}

View = 0b00000000000000000000000000000001
SendMessage = 0b00000000000000000000000000000010
ManageMessages =  0b00000000000000000000000000000100
ManageChannel = 0b00000000000000000000000000001000
VoiceCall = 0b00000000000000000000000000010000
InviteOthers = 0b00000000000000000000000000100000
EmbedLinks = 0b00000000000000000000000001000000
UploadFiles = 0b00000000000000000000000010000000

View + SendMessage + ManageMessages + ManageChannel +VoiceCall + InviteOthers + EmbedLinks + UploadFiles
export const ServerPermission = {
    View: 0b00000000000000000000000000000001,            // 1
    ManageRoles: 0b00000000000000000000000000000010,   // 2
    ManageChannels: 0b00000000000000000000000000000100,  // 4
    ManageServer: 0b00000000000000000000000000001000,    // 8
    KickMembers: 0b00000000000000000000000000010000,     // 16
    BanMembers: 0b00000000000000000000000000100000,      // 32
    ChangeNickname: 0b00000000000000000001000000000000,  // 4096
    ManageNicknames: 0b00000000000000000010000000000000, // 8192
    ChangeAvatar: 0b00000000000000000100000000000000,    // 16382
    RemoveAvatars: 0b00000000000000001000000000000000,   // 32768
}



export const UserPermission = {
    Access: 1 << 0,
    ViewProfile: 1 << 1,
    SendMessage: 1 << 2,
    Invite: 1 << 3,
}


export const U32_MAX = 2**32 - 1; // 4294967295

export const DEFAULT_PERMISSION_DM =
    ChannelPermission.View
    + ChannelPermission.SendMessage
    + ChannelPermission.ManageChannel
    + ChannelPermission.VoiceCall
    + ChannelPermission.InviteOthers
    + ChannelPermission.EmbedLinks
    + ChannelPermission.UploadFiles;

"""
