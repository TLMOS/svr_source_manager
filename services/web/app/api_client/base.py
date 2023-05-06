import requests
from pathlib import Path
from urllib.error import HTTPError

from flask import request

from app.config import settings


class Router:
    """Simple class to mimic FastAPI routing and make code more readable."""

    def __init__(self, prefix: Path):
        self.prefix = prefix

    def request(self, method: str, route: str,
                json: str | None = None, **kwargs) -> requests.Response:
        """
        Send request to data server.

        Args:
            method: HTTP method.
            route: Route to send request to.
            **kwargs: Params to send with request.
        """
        response = requests.request(
            method=method,
            url=f'{settings.api_url}/{self.prefix}/{route}',
            params=kwargs,
            json=json,
            headers={'Authorization': request.headers.get('Authorization')}
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
