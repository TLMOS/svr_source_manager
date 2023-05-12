import requests
from pathlib import Path
from urllib.error import HTTPError

from flask_login import current_user

from app.config import settings


class Router:
    """Simple class to mimic FastAPI routing and make code more readable."""

    def __init__(self, prefix: Path, authorized: bool = False):
        self.prefix = prefix
        self.authorized = authorized

    def request(self,
                method: str,
                route: str,
                params: dict = {},
                json: str | None = None,
                authorized: bool | None = None
                ) -> requests.Response:
        """
        Send request to data server.

        Args:
            method: HTTP method.
            route: Route to send request to.
            **kwargs: Params to send with request.
        """
        headers = {}
        if authorized is None:
            authorized = self.authorized
        if authorized:
            headers = {
                'X-User-Id': str(current_user.id),
                'X-User-Role': str(current_user.role.value)
            }
        response = requests.request(
            method=method,
            url=f'{settings.api_url}/{self.prefix}/{route}',
            params=params,
            json=json,
            headers=headers
        )
        if response.status_code != 200:
            raise HTTPError(
                url=response.url,
                code=response.status_code,
                msg=response.json()['detail'],
                hdrs=response.headers,
                fp=None
            )
        return response
