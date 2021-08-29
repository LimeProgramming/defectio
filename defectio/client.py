from __future__ import annotations

import asyncio
from .user import User
from .message import Message
from .server import Server
import sys
import traceback
from .http import HttpClient
import aiohttp
from typing import (
    Any,
    Callable,
    Sequence,
    TypeVar,
    Coroutine,
    TYPE_CHECKING,
    Optional,
    Dict,
    List,
    Tuple,
)
import logging

from .websocket import WebsocketHandler
from .utils import SequenceProxy
import signal
import msgpack

try:
    import orjson as json
except ImportError:
    import json

from .state import ConnectionState
from .http import HttpClient

Coro = TypeVar("Coro", bound=Callable[..., Coroutine[Any, Any, Any]])

logger = logging.getLogger("defectio")


def _cancel_tasks(loop: asyncio.AbstractEventLoop) -> None:
    tasks = {t for t in asyncio.all_tasks(loop=loop) if not t.done()}

    if not tasks:
        return

    logger.info("Cleaning up after %d tasks.", len(tasks))
    for task in tasks:
        task.cancel()

    loop.run_until_complete(asyncio.gather(*tasks, return_exceptions=True))
    logger.info("All tasks finished cancelling.")

    for task in tasks:
        if task.cancelled():
            continue
        if task.exception() is not None:
            loop.call_exception_handler(
                {
                    "message": "Unhandled exception during Client.run shutdown.",
                    "exception": task.exception(),
                    "task": task,
                }
            )


def _cleanup_loop(loop: asyncio.AbstractEventLoop) -> None:
    try:
        _cancel_tasks(loop)
        loop.run_until_complete(loop.shutdown_asyncgens())
    finally:
        logger.info("Closing the event loop.")
        loop.close()


class Client:
    def __init__(
        self,
        *,
        api_url: str = "https://api.revolt.chat",
        loop: Optional[asyncio.AbstractEventLoop] = None,
        **options: Any,
    ):
        self.websocket: WebsocketHandler
        self.api_url = api_url
        self.loop: asyncio.AbstractEventLoop = (
            asyncio.get_event_loop() if loop is None else loop
        )

        connector: Optional[aiohttp.BaseConnector] = options.pop("connector", None)
        # proxy: Optional[str] = options.pop("proxy", None)
        # proxy_auth: Optional[aiohttp.BasicAuth] = options.pop("proxy_auth", None)
        # unsync_clock: bool = options.pop("assume_unsync_clock", True)
        self.http: HttpClient = HttpClient(
            session=connector,
            api_url=self.api_url,
        )

        self._handlers: Dict[str, Callable] = {"ready": self._handle_ready}
        self._listeners: Dict[
            str, List[Tuple[asyncio.Future, Callable[..., bool]]]
        ] = {}

        self._enable_debug_events: bool = options.pop("enable_debug_events", False)
        self._connection: ConnectionState = self._get_state(**options)
        self._closed: bool = False
        self._ready: asyncio.Event = asyncio.Event()
        self._connection.get_websocket = self._get_websocket
        self._connection._get_client = lambda: self

        # TODO remove it
        self.session = aiohttp.ClientSession()

    # internals

    def _get_websocket(self) -> WebsocketHandler:
        return self.websocket

    def _get_state(self, **options: Any) -> ConnectionState:
        return ConnectionState(
            dispatch=self.dispatch,
            handlers=self._handlers,
            http=self.http,
            loop=self.loop,
            **options,
        )

    def _handle_ready(self) -> None:
        self._ready.set()

    @property
    def latency(self) -> float:
        """:class:`float`: Measures latency between a HEARTBEAT and a HEARTBEAT_ACK in seconds.
        This could be referred to as the Defectio WebSocket protocol latency.
        """
        ws = self.websocket
        return float("nan") if not ws else ws.latency

    # @property
    # def user(self) -> Optional[ClientUser]:
    #     """Optional[:class:`.ClientUser`]: Represents the connected client. ``None`` if not logged in."""
    #     return self._connection.user

    @property
    def servers(self) -> List[Server]:
        """List[:class:`.Server`]: The servers that the connected client is a member of."""
        return self._connection.servers

    # @property
    # def cached_messages(self) -> Sequence[Message]:
    #     """Sequence[:class:`.Message`]: Read-only list of messages the connected client has cached."""
    #     return utils.SequenceProxy(self._connection._messages or [])

    # @property
    # def private_channels(self) -> List[PrivateChannel]:
    #     """List[:class:`.abc.PrivateChannel`]: The private channels that the connected client is participating on."""
    #     return self._connection.private_channels

    def is_ready(self) -> bool:
        """:class:`bool`: Specifies if the client's internal cache is ready for use."""
        return self._ready.is_set()

    async def _run_event(
        self,
        coro: Callable[..., Coroutine[Any, Any, Any]],
        event_name: str,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        try:
            await coro(*args, **kwargs)
        except asyncio.CancelledError:
            pass
        except Exception:
            try:
                await self.on_error(event_name, *args, **kwargs)
            except asyncio.CancelledError:
                pass

    def _schedule_event(
        self,
        coro: Callable[..., Coroutine[Any, Any, Any]],
        event_name: str,
        *args: Any,
        **kwargs: Any,
    ) -> asyncio.Task:
        wrapped = self._run_event(coro, event_name, *args, **kwargs)
        # Schedules the task
        return asyncio.create_task(wrapped, name=f"defectio: {event_name}")

    def dispatch(self, event: str, *args: Any, **kwargs: Any) -> None:
        logger.debug("Dispatching event %s", event)
        method = "on_" + event
        listeners = self._listeners.get(event)
        if listeners:
            removed = []
            for i, (future, condition) in enumerate(listeners):
                if future.cancelled():
                    removed.append(i)
                    continue

                try:
                    result = condition(*args)
                except Exception as exc:
                    future.set_exception(exc)
                    removed.append(i)
                else:
                    if result:
                        if len(args) == 0:
                            future.set_result(None)
                        elif len(args) == 1:
                            future.set_result(args[0])
                        else:
                            future.set_result(args)
                        removed.append(i)

            if len(removed) == len(listeners):
                self._listeners.pop(event)
            else:
                for idx in reversed(removed):
                    del listeners[idx]
        try:
            coro = getattr(self, method)
        except AttributeError:
            pass
        else:
            self._schedule_event(coro, method, *args, **kwargs)

    async def on_error(self, event_method: str, *args: Any, **kwargs: Any) -> None:
        """|coro|
        The default error handler provided by the client.
        By default this prints to :data:`sys.stderr` however it could be
        overridden to have a different implementation.
        Check :func:`~discord.on_error` for more details.
        """
        print(f"Ignoring exception in {event_method}", file=sys.stderr)
        traceback.print_exc()

    # login state management

    async def start(self, token: str) -> None:
        """|coro|

        A shorthand coroutine for :meth:`login` + :meth:`connect`.

        Raises
        -------
        TypeError
            An unexpected keyword argument was received.
        """

        async with self.session.get(self.api_url) as resp:
            api_info = json.loads(await resp.text())

        self.api_info = api_info
        self.websocket = WebsocketHandler(
            self.session, token, api_info["ws"], client=self
        )
        self.http.token = token
        # self.http = HttpClient(self.session, self.token, self.api_url, self.api_info)

        await self.websocket.start()

    def run(self, *args: Any, **kwargs: Any) -> None:
        """A blocking call that abstracts away the event loop
        initialisation from you.

        If you want more control over the event loop then this
        function should not be used. Use :meth:`start` coroutine
        or :meth:`connect` + :meth:`login`.

        Roughly Equivalent to: ::

            try:
                loop.run_until_complete(start(*args, **kwargs))
            except KeyboardInterrupt:
                loop.run_until_complete(close())
                # cancel all tasks lingering
            finally:
                loop.close()

        .. warning::

            This function must be the last function to call due to the fact that it
            is blocking. That means that registration of events or anything being
            called after this function call will not execute until it returns.
        """
        loop = self.loop

        try:
            loop.add_signal_handler(signal.SIGINT, lambda: loop.stop())
            loop.add_signal_handler(signal.SIGTERM, lambda: loop.stop())
        except NotImplementedError:
            pass

        async def runner():
            try:
                await self.start(*args, **kwargs)
            finally:
                if not self.is_closed():
                    await self.close()
                pass

        def stop_loop_on_completion(f):
            loop.stop()

        future = asyncio.ensure_future(runner(), loop=loop)
        future.add_done_callback(stop_loop_on_completion)
        try:
            loop.run_forever()
        except KeyboardInterrupt:
            logger.info("Received signal to terminate bot and event loop.")
        finally:
            future.remove_done_callback(stop_loop_on_completion)
            logger.info("Cleaning up tasks.")

        if not future.cancelled():
            try:
                return future.result()
            except KeyboardInterrupt:
                return None

    # helpers/getters

    @property
    def users(self) -> List[User]:
        """List[:class:`~discord.User`]: Returns a list of all the users the bot can see."""
        return list(self._connection._users.values())

    # def get_channel(
    #     self, id: int, /
    # ) -> Optional[Union[GuildChannel, Thread, PrivateChannel]]:
    #     """Returns a channel or thread with the given ID.
    #     Parameters
    #     -----------
    #     id: :class:`int`
    #         The ID to search for.
    #     Returns
    #     --------
    #     Optional[Union[:class:`.abc.GuildChannel`, :class:`.Thread`, :class:`.abc.PrivateChannel`]]
    #         The returned channel or ``None`` if not found.
    #     """
    #     return self._connection.get_channel(id)

    def get_server(self, id: str, /) -> Optional[Server]:
        """Returns a serverr with the given ID.
        Parameters
        -----------
        id: :class:`str`
            The ID to search for.
        Returns
        --------
        Optional[:class:`.Server`]
            The guild or ``None`` if not found.
        """
        return self._connection._get_server(id)

    def get_user(self, id: str) -> Optional[User]:
        """Returns a user with the given ID.
        Parameters
        -----------
        id: :class:`str`
            The ID to search for.
        Returns
        --------
        Optional[:class:`~defectio.User`]
            The user or ``None`` if not found.
        """
        return self._connection.get_user(id)

    # def get_all_channels(self) -> Generator[GuildChannel, None, None]:
    #     """A generator that retrieves every :class:`.abc.GuildChannel` the client can 'access'.
    #     This is equivalent to: ::
    #         for guild in client.guilds:
    #             for channel in guild.channels:
    #                 yield channel
    #     .. note::
    #         Just because you receive a :class:`.abc.GuildChannel` does not mean that
    #         you can communicate in said channel. :meth:`.abc.GuildChannel.permissions_for` should
    #         be used for that.
    #     Yields
    #     ------
    #     :class:`.abc.GuildChannel`
    #         A channel the client can 'access'.
    #     """

    #     for guild in self.guilds:
    #         yield from guild.channels

    # def get_all_members(self) -> Generator[Member, None, None]:
    #     """Returns a generator with every :class:`.Member` the client can see.
    #     This is equivalent to: ::
    #         for guild in client.guilds:
    #             for member in guild.members:
    #                 yield member
    #     Yields
    #     ------
    #     :class:`.Member`
    #         A member the client can see.
    #     """
    #     for guild in self.guilds:
    #         yield from guild.members

    # listeners/waiters

    async def wait_until_ready(self) -> None:
        """|coro|
        Waits until the client's internal cache is all ready.
        """
        await self._ready.wait()

    def wait_for(
        self,
        event: str,
        *,
        check: Optional[Callable[..., bool]] = None,
        timeout: Optional[float] = None,
    ) -> Any:
        """|coro|
        Waits for a WebSocket event to be dispatched.
        This could be used to wait for a user to reply to a message,
        or to react to a message, or to edit a message in a self-contained
        way.
        The ``timeout`` parameter is passed onto :func:`asyncio.wait_for`. By default,
        it does not timeout. Note that this does propagate the
        :exc:`asyncio.TimeoutError` for you in case of timeout and is provided for
        ease of use.
        In case the event returns multiple arguments, a :class:`tuple` containing those
        arguments is returned instead. Please check the
        :ref:`documentation <discord-api-events>` for a list of events and their
        parameters.
        This function returns the **first event that meets the requirements**.
        Examples
        ---------
        Waiting for a user reply: ::
            @client.event
            async def on_message(message):
                if message.content.startswith('$greet'):
                    channel = message.channel
                    await channel.send('Say hello!')
                    def check(m):
                        return m.content == 'hello' and m.channel == channel
                    msg = await client.wait_for('message', check=check)
                    await channel.send(f'Hello {msg.author}!')
        Parameters
        ------------
        event: :class:`str`
            The event name, similar to the :ref:`event reference <discord-api-events>`,
            but without the ``on_`` prefix, to wait for.
        check: Optional[Callable[..., :class:`bool`]]
            A predicate to check what to wait for. The arguments must meet the
            parameters of the event being waited for.
        timeout: Optional[:class:`float`]
            The number of seconds to wait before timing out and raising
            :exc:`asyncio.TimeoutError`.
        Raises
        -------
        asyncio.TimeoutError
            If a timeout is provided and it was reached.
        Returns
        --------
        Any
            Returns no arguments, a single argument, or a :class:`tuple` of multiple
            arguments that mirrors the parameters passed in the
            :ref:`event reference <discord-api-events>`.
        """

        future = self.loop.create_future()
        if check is None:

            def _check(*args):
                return True

            check = _check

        ev = event.lower()
        try:
            listeners = self._listeners[ev]
        except KeyError:
            listeners = []
            self._listeners[ev] = listeners

        listeners.append((future, check))
        return asyncio.wait_for(future, timeout)

        # event registration

    def event(self, coro: Coro) -> Coro:
        """A decorator that registers an event to listen to.
        You can find more info about the events on the :ref:`documentation below <discord-api-events>`.
        The events must be a :ref:`coroutine <coroutine>`, if not, :exc:`TypeError` is raised.
        Example
        ---------
        .. code-block:: python3
            @client.event
            async def on_ready():
                print('Ready!')
        Raises
        --------
        TypeError
            The coroutine passed is not actually a coroutine.
        """

        if not asyncio.iscoroutinefunction(coro):
            raise TypeError("event registered must be a coroutine function")

        setattr(self, coro.__name__, coro)
        logger.debug("%s has successfully been registered as an event", coro.__name__)
        return coro

    @property
    def user(self) -> Optional[User]:
        """Optional[:class:`.ClientUser`]: Represents the connected client. ``None`` if not logged in."""
        return self._connection.user
