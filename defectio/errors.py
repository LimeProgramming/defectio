from __future__ import annotations

from typing import Any
from typing import Optional
from typing import TYPE_CHECKING
from typing import Union

if TYPE_CHECKING:
    from aiohttp import ClientResponse

    try:
        from requests import Response

        _ResponseType = Union[ClientResponse, Response]
    except ModuleNotFoundError:
        _ResponseType = ClientResponse


class DefectioException(Exception):
    """Base exception class for defectio

    Ideally speaking, this could be caught to handle any exceptions raised from this library.
    """

    pass


class ClientException(DefectioException):
    """Exception that's raised when an operation in the :class:`Client` fails.

    These are usually for exceptions that happened due to user input.
    """

    pass


class GatewayNotFound(DefectioException):
    """Exception that's raised when the gateway is not found."""

    pass


def _flatten_error_dict(d: dict[str, Any], key: str = "") -> dict[str, str]:
    items: list[tuple[str, str]] = []
    for k, v in d.items():
        new_key = key + "." + k if key else k

        if isinstance(v, dict):
            try:
                _errors: list[dict[str, Any]] = v["_errors"]
            except KeyError:
                items.extend(_flatten_error_dict(v, new_key).items())
            else:
                items.append((new_key, " ".join(x.get("message", "") for x in _errors)))
        else:
            items.append((new_key, v))

    return dict(items)


class HTTPException(DefectioException):
    """Exception that's raised when an HTTP request operation fails.

    Attributes
    ------------
    response: :class:`aiohttp.ClientResponse`
        The response of the failed HTTP request. This is an
        instance of :class:`aiohttp.ClientResponse`. In some cases
        this could also be a :class:`requests.Response`.

    text: :class:`str`
        The text of the error. Could be an empty string.
    status: :class:`int`
        The status code of the HTTP request.
    code: :class:`int`
        The Revolt specific error code for the failure.
    """

    def __init__(
        self, response: _ResponseType, message: Optional[Union[str, dict[str, Any]]]
    ):
        self.response: _ResponseType = response
        self.status: int = response.status  # type: ignore
        self.code: int
        self.text: str
        if isinstance(message, dict):
            self.code = message.get("code", 0)
            base = message.get("message", "")
            errors = message.get("errors")
            if errors:
                errors = _flatten_error_dict(errors)
                helpful = "\n".join("In %s: %s" % t for t in errors.items())
                self.text = base + "\n" + helpful
            else:
                self.text = base
        else:
            self.text = message or ""
            self.code = 0

        fmt = "{0.status} {0.reason} (error code: {1})"
        if len(self.text):
            fmt += ": {2}"

        super().__init__(fmt.format(self.response, self.code, self.text))


class NotFound(HTTPException):
    """Exception that's raised for when status code 404 occurs.
    Subclass of :exc:`HTTPException`
    """

    pass


class Forbidden(HTTPException):
    """Exception that's raised for when status code 403 occurs.

    Subclass of :exc:`HTTPException`
    """

    pass


class RevoltServerError(HTTPException):
    """Exception that's raised for when a 500 range status code occurs.

    Subclass of :exc:`HTTPException`.
    """

    pass


class InvalidData(ClientException):
    """Exception that's raised when the library encounters unknown

    or invalid data from Revolt.
    """

    pass


class InvalidArgument(ClientException):
    """Exception that's raised when an argument to a function
    is invalid some way (e.g. wrong value or wrong type).

    This could be considered the analogous of ``ValueError`` and
    ``TypeError`` except inherited from :exc:`ClientException` and thus
    :exc:`RevoltException`.
    """

    pass


class LoginFailure(ClientException):
    """Exception that's raised when the :meth:`Client.login` function
    fails to log you in from improper credentials or some other misc.
    failure.
    """

    pass
