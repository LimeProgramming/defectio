import collections
import datetime
from typing import Any
from typing import AsyncIterator
from typing import Callable
from typing import Generic
from typing import Iterable
from typing import Iterator
from typing import Optional
from typing import Sequence
from inspect import signature as _signature, isawaitable as _isawaitable
from typing import TypeVar
from typing import Union, Protocol, TYPE_CHECKING, Mapping, ForwardRef, Literal
from operator import attrgetter
import sys
import re
import unicodedata


PY_310 = sys.version_info >= (3, 10)

_IS_ASCII = re.compile(r"^[\x00-\x7f]+$")


def _string_width(string: str, *, _IS_ASCII=_IS_ASCII) -> int:
    """Returns string's width."""
    match = _IS_ASCII.match(string)
    if match:
        return match.endpos

    UNICODE_WIDE_CHAR_TYPE = "WFA"
    func = unicodedata.east_asian_width
    return sum(2 if func(char) in UNICODE_WIDE_CHAR_TYPE else 1 for char in string)


def flatten_literal_params(parameters: Iterable[Any]) -> tuple[Any, ...]:
    params = []
    literal_cls = type(Literal[0])
    for p in parameters:
        if isinstance(p, literal_cls):
            params.extend(p.__args__)
        else:
            params.append(p)
    return tuple(params)


def normalise_optional_params(parameters: Iterable[Any]) -> tuple[Any, ...]:
    none_cls = type(None)
    return tuple(p for p in parameters if p is not none_cls) + (none_cls,)


def evaluate_annotation(
    tp: Any,
    globals: dict[str, Any],
    locals: dict[str, Any],
    cache: dict[str, Any],
    *,
    implicit_str: bool = True,
):
    if isinstance(tp, ForwardRef):
        tp = tp.__forward_arg__
        # ForwardRefs always evaluate their internals
        implicit_str = True

    if implicit_str and isinstance(tp, str):
        if tp in cache:
            return cache[tp]
        evaluated = eval(tp, globals, locals)
        cache[tp] = evaluated
        return evaluate_annotation(evaluated, globals, locals, cache)

    if hasattr(tp, "__args__"):
        implicit_str = True
        is_literal = False
        args = tp.__args__
        if not hasattr(tp, "__origin__"):
            if PY_310 and tp.__class__ is types.UnionType:  # type: ignore
                converted = Union[args]  # type: ignore
                return evaluate_annotation(converted, globals, locals, cache)

            return tp
        if tp.__origin__ is Union:
            try:
                if args.index(type(None)) != len(args) - 1:
                    args = normalise_optional_params(tp.__args__)
            except ValueError:
                pass
        if tp.__origin__ is Literal:
            if not PY_310:
                args = flatten_literal_params(tp.__args__)
            implicit_str = False
            is_literal = True

        evaluated_args = tuple(
            evaluate_annotation(arg, globals, locals, cache, implicit_str=implicit_str)
            for arg in args
        )

        if is_literal and not all(
            isinstance(x, (str, int, bool, type(None))) for x in evaluated_args
        ):
            raise TypeError(
                "Literal arguments must be of type str, int, bool, or NoneType."
            )

        if evaluated_args == args:
            return tp

        try:
            return tp.copy_with(evaluated_args)
        except AttributeError:
            return tp.__origin__[evaluated_args]

    return tp


class _cached_property:
    def __init__(self, function):
        self.function = function
        self.__doc__ = getattr(function, "__doc__")

    def __get__(self, instance, owner):
        if instance is None:
            return self

        value = self.function(instance)
        setattr(instance, self.function.__name__, value)

        return value


if TYPE_CHECKING:
    from functools import cached_property as cached_property

    from typing_extensions import ParamSpec

    class _RequestLike(Protocol):
        headers: Mapping[str, Any]

    P = ParamSpec("P")

else:
    cached_property = _cached_property

T = TypeVar("T")
T_co = TypeVar("T_co", covariant=True)
_Iter = Union[Iterator[T], AsyncIterator[T]]


def copy_doc(original: Callable) -> Callable[[T], T]:
    def decorator(overriden: T) -> T:
        overriden.__doc__ = original.__doc__
        overriden.__signature__ = _signature(original)  # type: ignore
        return overriden

    return decorator


class _MissingSentinel:
    def __eq__(self, other):
        return False

    def __bool__(self):
        return False

    def __repr__(self):
        return "..."


MISSING: Any = _MissingSentinel()


class SequenceProxy(Generic[T_co], collections.abc.Sequence):
    """Read-only proxy of a Sequence."""

    def __init__(self, proxied: Sequence[T_co]):
        self.__proxied = proxied

    def __getitem__(self, idx: int) -> T_co:
        return self.__proxied[idx]

    def __len__(self) -> int:
        return len(self.__proxied)

    def __contains__(self, item: Any) -> bool:
        return item in self.__proxied

    def __iter__(self) -> Iterator[T_co]:
        return iter(self.__proxied)

    def __reversed__(self) -> Iterator[T_co]:
        return reversed(self.__proxied)

    def index(self, value: Any, *args, **kwargs) -> int:
        return self.__proxied.index(value, *args, **kwargs)

    def count(self, value: Any) -> int:
        return self.__proxied.count(value)


def find(predicate: Callable[[T], Any], seq: Iterable[T]) -> Optional[T]:
    for element in seq:
        if predicate(element):
            return element
    return None


def compute_timedelta(dt: datetime.datetime):
    if dt.tzinfo is None:
        dt = dt.astimezone()
    now = datetime.datetime.now(datetime.timezone.utc)
    return max((dt - now).total_seconds(), 0)


def get(iterable: Iterable[T], **attrs: Any) -> Optional[T]:
    r"""A helper that returns the first element in the iterable that meets
    all the traits passed in ``attrs``. This is an alternative for
    :func:`~discord.utils.find`.
    When multiple attributes are specified, they are checked using
    logical AND, not logical OR. Meaning they have to meet every
    attribute passed in and not one of them.
    To have a nested attribute search (i.e. search by ``x.y``) then
    pass in ``x__y`` as the keyword argument.
    If nothing is found that matches the attributes passed, then
    ``None`` is returned.
    Examples
    ---------
    Basic usage:
    .. code-block:: python3
        member = discord.utils.get(message.guild.members, name='Foo')
    Multiple attribute matching:
    .. code-block:: python3
        channel = discord.utils.get(guild.voice_channels, name='Foo', bitrate=64000)
    Nested attribute matching:
    .. code-block:: python3
        channel = discord.utils.get(client.get_all_channels(), guild__name='Cool', name='general')
    Parameters
    -----------
    iterable
        An iterable to search through.
    \*\*attrs
        Keyword arguments that denote attributes to search with.
    """

    # global -> local
    _all = all
    attrget = attrgetter

    # Special case the single element call
    if len(attrs) == 1:
        k, v = attrs.popitem()
        pred = attrget(k.replace("__", "."))
        for elem in iterable:
            if pred(elem) == v:
                return elem
        return None

    converted = [
        (attrget(attr.replace("__", ".")), value) for attr, value in attrs.items()
    ]

    for elem in iterable:
        if _all(pred(elem) == value for pred, value in converted):
            return elem
    return None


async def maybe_coroutine(f, *args, **kwargs):
    value = f(*args, **kwargs)
    if _isawaitable(value):
        return await value
    else:
        return value


def resolve_annotation(
    annotation: Any,
    globalns: dict[str, Any],
    localns: Optional[dict[str, Any]],
    cache: Optional[dict[str, Any]],
) -> Any:
    if annotation is None:
        return type(None)
    if isinstance(annotation, str):
        annotation = ForwardRef(annotation)

    locals = globalns if localns is None else localns
    if cache is None:
        cache = {}
    return evaluate_annotation(annotation, globalns, locals, cache)
