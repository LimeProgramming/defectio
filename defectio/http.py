from __future__ import annotations

import sys

from typing import TYPE_CHECKING, Optional
from . import __version__
import ulid
import logging
import aiohttp

if TYPE_CHECKING:
    import aiohttp

logger = logging.getLogger("revolt")


class HttpClient:
    def __init__(
        self,
        session: aiohttp.ClientSession,
        api_url: str,
    ):
        self.session = session if session is not None else aiohttp.ClientSession()
        self.token: Optional[str] = None
        # self.api_info = api_info
        self.api_url = api_url
        user_agent = "Defectio (https://github.com/Darkflame72/defectio {0}) Python/{1[0]}.{1[1]} aiohttp/{2}"
        self.user_agent: str = user_agent.format(
            __version__, sys.version_info, aiohttp.__version__
        )
        self.is_bot = True

    async def request(self, method: str, path: str, auth_needed=True, **kwargs):
        url = f"{self.api_url}/{path}"
        headers = kwargs.get("headers", {})
        headers["User-Agent"] = self.user_agent
        if auth_needed:
            if self.is_bot and self.token is not None:
                headers["x-bot-token"] = self.token
            else:
                raise Exception("Not authenticated")
        headers["Content-Type"] = "application/json"
        kwargs["headers"] = headers

        # Generate nonce for post messages
        if method == "POST":
            kwargs["json"] = kwargs.get("json", {})
            kwargs["json"]["nonce"] = ulid.new().str

        async with self.session.request(method, url, **kwargs) as response:
            data = await response.json()
            if 300 > response.status >= 200:
                logger.debug("%s %s has received %s", method, url, data)
                return data

    async def close(self) -> None:
        if self.session:
            await self.session.close()

    async def node_info(self):
        path = ""
        return await self.request("GET", path, auth_needed=False)

    ################
    ## Onboarding ##
    ################

    async def check_onboarding(self):
        path = "onboard/hello"
        return await self.request("GET", path)

    async def complete_onboarding(self, username: str):
        path = "onboard/complete"
        return await self.request("GET", path, json={"username": username})

    ##########
    ## Auth ##
    ##########

    async def create_account(self, email: str, password: str, **kwargs):
        path = "auth/create"
        kwargs["email"] = email
        kwargs["password"] = password
        return await self.request("POST", path, json=kwargs, auth_needed=False)

    async def resend_verification(self, email: str, **kwargs) -> None:
        path = "auth/resend"
        kwargs["email"] = email
        return await self.request("POST", path, json=kwargs, auth_needed=False)

    async def login(self, email: str, password: str, **kwargs):
        path = "auth/login"
        kwargs["email"] = email
        kwargs["password"] = password
        return await self.request(
            "POST", path, json={"email": email, "password": password}, auth_needed=False
        )

    async def send_password_reset(self, email: str, **kwargs):
        path = "auth/send_reset"
        kwargs["email"] = email
        return await self.request("POST", path, json=kwargs, auth_needed=False)

    async def confirm_password_reset(self, password: str, token: str):
        path = "/auth/reset"
        return await self.request(
            "POST", path, json={"password": password, "token": token}, auth_needed=False
        )

    async def fetch_account(self):
        path = "auth/user"
        return await self.request("GET", path)

    async def check_auth(self):
        path = "auth/check"
        return await self.request("GET", path)

    async def change_password(self, old_password: str, new_password: str):
        path = "auth/change/password"
        return await self.request(
            "POST",
            path,
            json={"password": old_password, "new_password": new_password},
        )

    async def change_email(self, password: str, email: str):
        path = "auth/change/email"
        return await self.request("POST", path, json={"email": email})

    async def delete_session(self, session_id: str):
        path = f"auth/sessions/{session_id}"
        return await self.request("POST", path)

    async def fetch_sessions(self):
        path = "auth/sessions"
        return await self.request("GET", path)

    async def logout(self):
        path = "auth/logout"
        return await self.request("POST", path)

    ######################
    ## User Information ##
    ######################

    ## Self

    async def edit_self(self, **kwargs):
        path = "users/@me"
        return await self.request("PATCH", path, json=kwargs)

    async def change_username(self, username: str, password: str):
        path = "users/@me/username"
        return await self.request(
            "PATCH", path, json={"username": username, "password": password}
        )

    ## Users

    async def fetch_user(self, user_id: str):
        path = f"users/{user_id}"
        return await self.request("GET", path)

    async def fetch_user_profile(self, user_id: str):
        path = f"users/{user_id}/profile"
        return await self.request("GET", path)

    async def fetch_user_default_avatar(self, user_id: str):
        path = f"users/{user_id}/default_avatar"
        return await self.request("GET", path)

    async def fetch_mutual_friends(self, user_id: str):
        path = f"users/{user_id}/mutual_friends"
        return await self.request("GET", path)

    ######################
    ## Direct Messaging ##
    ######################

    async def fetch_dms(self):
        path = "users/dms"
        return await self.request("GET", path)

    async def open_dm(self, user_id: str):
        path = f"users/{user_id}/dm"
        return await self.request("POST", path)

    ###################
    ## Relationships ##
    ###################

    async def fetch_relationships(self):
        path = "users/relationships"
        return await self.request("GET", path)

    async def fetch_relationship(self, user_id: str):
        path = f"users/{user_id}/relationships"
        return await self.request("GET", path)

    async def friend_request(self, user_id: str):
        path = f"users/{user_id}/friend"
        return await self.request("PUT", path)

    async def remove_friend(self, user_id: str):
        path = f"users/{user_id}/friend"
        return await self.request("DELETE", path)

    async def block_user(self, user_id: str):
        path = f"users/{user_id}/block"
        return await self.request("PUT", path)

    async def unblock_user(self, user_id: str):
        path = f"users/{user_id}/block"
        return await self.request("DELETE", path)

    #########################
    ## Channel Information ##
    #########################

    ######

    async def send_message(self, channel_id: str, content: str):
        path = f"channels/{channel_id}/messages"
        return await self.request("POST", path, json={"content": content})
