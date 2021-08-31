from __future__ import annotations

import asyncio
import logging
import signal
import sys
import traceback
from typing import Any
from typing import Callable
from typing import Coroutine
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple
from typing import TYPE_CHECKING
from typing import TypeVar

import aiohttp

from . import __version__
from .gateway import DefectioWebsocket
from .http import DefectioHTTP
from .models import User
from .state import ConnectionState

if TYPE_CHECKING:
    pass

__all__ = ("Client",)

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
        api_url: Optional[str] = "https://api.revolt.chat",
        loop: Optional[asyncio.AbstractEventLoop] = None,
        **kwargs: Any,
    ) -> None:

        self.api_url: str = api_url
        self.loop: asyncio.AbstractEventLoop = (
            asyncio.get_event_loop() if loop is None else loop
        )

        self.websocket: DefectioWebsocket
        self.http: DefectioHTTP
        self.session = kwargs.pop("session", None)

        self._handlers: Dict[str, Callable] = {"ready": self._handle_ready}
        self._listeners: Dict[
            str, List[Tuple[asyncio.Future, Callable[..., bool]]]
        ] = {}

        self._ready = asyncio.Event()
        self._closed = True
        self._connection: ConnectionState = self._get_state(**kwargs)

    def _get_state(self, **options: Any) -> ConnectionState:
        return ConnectionState(
            dispatch=self.dispatch,
            handlers=self._handlers,
            http=self.get_http,
            websocket=self.get_websocket,
            loop=self.loop,
            **options,
        )

    def _handle_ready(self) -> None:
        self._ready.set()

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
        """
        print(f"Ignoring exception in {event_method}", file=sys.stderr)
        traceback.print_exc()

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

    ################
    ## Properties ##
    ################

    @property
    def user(self) -> Optional[User]:
        """Optional[:class:`.ClientUser`]: Represents the connected client. ``None`` if not logged in."""
        return self._connection.user

    def get_http(self) -> DefectioHTTP:
        return self.http

    def get_websocket(self) -> DefectioWebsocket:
        return self.websocket

    #############
    ## Getters ##
    #############

    def get_channel(self, channel_id: str):
        channel = self._connection.get_channel(channel_id)
        return channel

    ######################
    ## State Management ##
    ######################

    def is_closed(self):
        return self.websocket.closed and self.session.closed

    async def close(self) -> None:
        if self._closed:
            return

        self._closed = True
        if self.websocket is not None:
            await self.websocket.close()

        if self.session is not None:
            await self.session.close()

    async def create(self) -> None:
        user_agent = "Defectio (https://github.com/Darkflame72/defectio {0}) Python/{1[0]}.{1[1]} aiohttp/{2}".format(
            __version__, sys.version_info, aiohttp.__version__
        )
        self.session = aiohttp.ClientSession()
        self.http = DefectioHTTP(self.session, self.api_url, user_agent)
        api_info = await self.http.node_info()
        self._connection.set_api_info(api_info)
        self.websocket = DefectioWebsocket(
            self.session, api_info["ws"], user_agent, self
        )

    async def connect(self) -> None:
        self._closed = False

    async def login(self, token: str) -> None:
        self.http.login(token)
        await self.websocket.connect(token)

    async def start(self, token: str):
        await self.create()
        await self.login(token)
        await self.connect()

    def run(self, *args: Any, **kwargs: Any) -> None:
        loop = self.loop

        try:
            loop.add_signal_handler(signal.SIGINT, loop.stop)
            loop.add_signal_handler(signal.SIGTERM, loop.stop)
        except NotImplementedError:
            pass

        async def runner() -> None:
            try:
                await self.start(*args, **kwargs)
            finally:
                if not self.is_closed():
                    await self.close()

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
            _cleanup_loop(loop)
