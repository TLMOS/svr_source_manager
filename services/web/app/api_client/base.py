import requests
from pathlib import Path
from urllib.error import HTTPError

from flask_login import current_user

from app.config import settings
from app.schemas import UserRole


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
        if authorized is None:
            # Use class default value
            authorized = self.authorized
        if authorized and current_user.role == UserRole.ADMIN:
            # X-User-ID header adds only restrictions, so we don't need
            # to add it for admin user
            authorized = False
        response = requests.request(
            method=method,
            url=f'{settings.api_url}/{self.prefix}/{route}',
            params=params,
            json=json,
            headers={'X-User-ID': str(current_user.id)} if authorized else None
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
