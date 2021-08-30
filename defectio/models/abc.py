from __future__ import annotations

import sys
import copy
import asyncio
from typing import Any, Protocol, runtime_checkable, Optional, TYPE_CHECKING, Dict

if TYPE_CHECKING:
    from .state import ConnectionState
    from .server import Server


@runtime_checkable
class User(Protocol):
    """An ABC that details the common operations on a Discord user.
    The following implement this ABC:
    - :class:`~defectio.User`
    - :class:`~defectio.ClientUser`
    - :class:`~defectio.Member`
    Attributes
    -----------
    name: :class:`str`
        The user's username.
    bot: :class:`bool`
        If the user is a bot account.
    """

    __slots__ = ()

    name: str
    bot: bool

    @property
    def display_name(self) -> str:
        """:class:`str`: Returns the user's display name."""
        raise NotImplementedError

    @property
    def mention(self) -> str:
        """:class:`str`: Returns a string that allows you to mention the given user."""
        raise NotImplementedError


class ServerChannel:
    __slots__ = ()

    id: int
    name: str
    server: Server
    type: str
    position: int
    category_id: Optional[int]
    _state: ConnectionState

    if TYPE_CHECKING:

        def __init__(
            self, *, state: ConnectionState, server: Server, data: Dict[str, Any]
        ):
            ...

    def __str__(self) -> str:
        return self.name

    def _update(self, server: Server, data: Dict[str, Any]) -> None:
        raise NotImplementedError

    async def delete(self, *, reason: Optional[str] = None) -> None:
        """|coro|
        Deletes the channel.
        You must have :attr:`~discord.Permissions.manage_channels` permission to use this.
        Parameters
        -----------
        reason: Optional[:class:`str`]
            The reason for deleting this channel.
            Shows up on the audit log.
        Raises
        -------
        ~discord.Forbidden
            You do not have proper permissions to delete the channel.
        ~discord.NotFound
            The channel was not found or was already deleted.
        ~discord.HTTPException
            Deleting the channel failed.
        """
        await self._state.http.close_channel(self.id)


class Messageable(Protocol):
    """An ABC that details the common operations on a model that can send messages.
    The following implement this ABC:
    - :class:`~discord.TextChannel`
    - :class:`~discord.DMChannel`
    - :class:`~discord.GroupChannel`
    - :class:`~discord.User`
    - :class:`~discord.Member`
    - :class:`~discord.ext.commands.Context`
    Note
    ----
    This ABC is not decorated with :func:`typing.runtime_checkable`, so will fail :func:`isinstance`/:func:`issubclass`
    checks.
    """

    __slots__ = ()
    _state: ConnectionState

    async def _get_channel(self):
        raise NotImplementedError

    async def send(
        self,
        content=None,
        *,
        file=None,
        files=None,
        delete_after=None,
        nonce=None,
        allowed_mentions=None,
        reference=None,
        mention_author=None,
    ):
        """|coro|
        Sends a message to the destination with the content given.
        The content must be a type that can convert to a string through ``str(content)``.
        If the content is set to ``None`` (the default), then the ``embed`` parameter must
        be provided.
        To upload a single file, the ``file`` parameter should be used with a
        single :class:`~discord.File` object. To upload multiple files, the ``files``
        parameter should be used with a :class:`list` of :class:`~discord.File` objects.
        **Specifying both parameters will lead to an exception**.
        If the ``embed`` parameter is provided, it must be of type :class:`~discord.Embed` and
        it must be a rich embed type.
        Parameters
        ------------
        content: :class:`str`
            The content of the message to send.
        embed: :class:`~discord.Embed`
            The rich embed for the content.
        file: :class:`~discord.File`
            The file to upload.
        files: List[:class:`~discord.File`]
            A list of files to upload. Must be a maximum of 10.
        nonce: :class:`int`
            The nonce to use for sending this message. If the message was successfully sent,
            then the message will have a nonce with this value.
        delete_after: :class:`float`
            If provided, the number of seconds to wait in the background
            before deleting the message we just sent. If the deletion fails,
            then it is silently ignored.
        allowed_mentions: :class:`~discord.AllowedMentions`
            Controls the mentions being processed in this message. If this is
            passed, then the object is merged with :attr:`~discord.Client.allowed_mentions`.
            The merging behaviour only overrides attributes that have been explicitly passed
            to the object, otherwise it uses the attributes set in :attr:`~discord.Client.allowed_mentions`.
            If no object is passed at all then the defaults given by :attr:`~discord.Client.allowed_mentions`
            are used instead.
            .. versionadded:: 1.4
        reference: Union[:class:`~discord.Message`, :class:`~discord.MessageReference`]
            A reference to the :class:`~discord.Message` to which you are replying, this can be created using
            :meth:`~discord.Message.to_reference` or passed directly as a :class:`~discord.Message`. You can control
            whether this mentions the author of the referenced message using the :attr:`~discord.AllowedMentions.replied_user`
            attribute of ``allowed_mentions`` or by setting ``mention_author``.
            .. versionadded:: 1.6
        mention_author: Optional[:class:`bool`]
            If set, overrides the :attr:`~discord.AllowedMentions.replied_user` attribute of ``allowed_mentions``.
            .. versionadded:: 1.6
        Raises
        --------
        ~discord.HTTPException
            Sending the message failed.
        ~discord.Forbidden
            You do not have the proper permissions to send the message.
        ~discord.InvalidArgument
            The ``files`` list is not of the appropriate size,
            you specified both ``file`` and ``files``,
            or the ``reference`` object is not a :class:`~discord.Message`
            or :class:`~discord.MessageReference`.
        Returns
        ---------
        :class:`~discord.Message`
            The message that was sent.
        """

        channel = await self._get_channel()
        state = self._state
        content = str(content) if content is not None else None

        # if mention_author is not None:
        #     allowed_mentions = allowed_mentions or AllowedMentions().to_dict()
        #     allowed_mentions["replied_user"] = bool(mention_author)

        # if reference is not None:
        #     try:
        #         reference = reference.to_message_reference_dict()
        #     except AttributeError:
        #         raise InvalidArgument(
        #             "reference parameter must be Message or MessageReference"
        #         ) from None

        # if file is not None and files is not None:
        #     raise InvalidArgument("cannot pass both file and files parameter to send()")

        # if file is not None:
        #     if not isinstance(file, File):
        #         raise InvalidArgument("file parameter must be File")

        #     try:
        #         data = await state.http.send_files(
        #             channel.id,
        #             files=[file],
        #             allowed_mentions=allowed_mentions,
        #             content=content,
        #             embed=embed,
        #             nonce=nonce,
        #             message_reference=reference,
        #         )
        #     finally:
        #         file.close()

        # elif files is not None:
        #     if len(files) > 10:
        #         raise InvalidArgument(
        #             "files parameter must be a list of up to 10 elements"
        #         )
        #     elif not all(isinstance(file, File) for file in files):
        #         raise InvalidArgument("files parameter must be a list of File")

        #     try:
        #         data = await state.http.send_files(
        #             channel.id,
        #             files=files,
        #             content=content,
        #             tts=tts,
        #             embed=embed,
        #             nonce=nonce,
        #             allowed_mentions=allowed_mentions,
        #             message_reference=reference,
        #         )
        #     finally:
        #         for f in files:
        #             f.close()
        # else:
        data = await state.http.send_message(
            channel.id,
            content,
        )

        ret = state.create_message(channel=channel, data=data)
        await self.stop_typing()
        # if delete_after is not None:
        #     await ret.delete(delay=delete_after)
        return ret

    async def fetch_message(self, id):
        """|coro|
        Retrieves a single :class:`~discord.Message` from the destination.
        This can only be used by bot accounts.
        Parameters
        ------------
        id: :class:`int`
            The message ID to look for.
        Raises
        --------
        ~discord.NotFound
            The specified message was not found.
        ~discord.Forbidden
            You do not have the permissions required to get a message.
        ~discord.HTTPException
            Retrieving the message failed.
        Returns
        --------
        :class:`~discord.Message`
            The message asked for.
        """

        channel = await self._get_channel()
        data = await self._state.http.get_message(channel.id, id)
        return self._state.create_message(channel=channel, data=data)

    async def start_typing(self):
        channel = await self._get_channel()
        await self._state.get_websocket().begin_typing(channel.id)

    async def stop_typing(self):
        channel = await self._get_channel()
        await self._state.get_websocket().stop_typing(channel.id)
