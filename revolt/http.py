from __future__ import annotations

import sys

from typing import TYPE_CHECKING
from . import __version__
import ulid

if TYPE_CHECKING:
    import aiohttp
    from .payloads import ApiInfo


class HttpClient:
    def __init__(
        self,
        session: aiohttp.ClientSession,
        token: str,
        api_url: str,
        api_info: ApiInfo,
    ):
        self.session = session
        self.token = token
        self.api_info = api_info
        self.api_url = api_url
        user_agent = "Revolt.py (https://github.com/Darkflame72/revolt.py {0}) Python/{1[0]}.{1[1]} aiohttp/{2}"
        self.user_agent: str = user_agent.format(
            __version__, sys.version_info, aiohttp.__version__
        )

    async def request(self, method: str, url: str, **kwargs):
        headers = kwargs.get("headers", {})
        headers["User-Agent"] = self.user_agent
        headers["x-bot-token"] = self.token
        kwargs["headers"] = headers

        # Generate nonce for post messages
        if method == "POST":
            kwargs["json"] = kwargs.get("json", {})
            kwargs["json"]["nonce"] = ulid.new().str

        async with self.session.request(method, url, **kwargs) as resp:
            return resp

    async def send_message(self, channel_id: str, content: str):
        url = f"{self.api_url}/channels/{channel_id}/messages"
        return await self.request("POST", url, json={"content": content})
