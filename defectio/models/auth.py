from typing import TYPE_CHECKING
from typing import Union
from ..types.payloads import LoginPayload


class Auth:
    def __init__(self, data: Union[LoginPayload, str]):
        try:
            self.user_id = data["user_id"]
            self.session_token = data["session_token"]
            self.is_bot = False
            self.token = None
        except TypeError:
            self.token = str(data)
            self.is_bot = True

    @property
    def headers(self):
        if self.is_bot is True:
            return {"x-bot-token": self.token}
        return {"x-user-id": self.user_id, "x-session-token": self.session_token}

    @property
    def payload(self):
        if self.is_bot is True:
            return {"token": self.token}
        return {"user_id": self.user_id, "session_token": self.session_token}
