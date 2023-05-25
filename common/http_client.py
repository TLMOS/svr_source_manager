from typing import Optional, Callable, Any
from contextlib import asynccontextmanager
from dataclasses import dataclass

import aiohttp

from common.utils import is_async_callable


def concat_url(url: str, route: str) -> str:
    """Concatenate url and route."""
    if url[-1] != '/':
        url += '/'
    route = route.strip('/')
    return url + route


@dataclass
class ClientRequest:
    route: str
    headers: dict[str, str]
    params: dict[str, Any]
    json: Optional[dict[str, Any]]

    def __post_init__(self):
        if self.headers is None:
            self.headers = {}
        if self.params is None:
            self.params = {}


class AsyncClientSession:
    """
    Async aiohttp session wrapper with lifecycle callbacks and middleware.

    Parameters:
    - url (str): base url

    Usage:
    ```python
    session = AsyncClientSession('http://example.com')

    @session.on_startup
    def on_startup():
        print('Session started')

    @session.on_shutdown
    async def on_shutdown():
        print('Session closed')

    async def ping():
        async with session.request('ping', method='GET') as response:
            print(await response.text())

    async def say_hello():
        await session.request_no_response('say_hello', method='POST')
    ```
    """

    def __init__(self, url: str):
        self.url = url
        self._is_opened = False
        self._session: Optional[aiohttp.ClientSession] = None

        self._on_startup: Optional[Callable] = None
        self._on_shutdown: Optional[Callable] = None
        self._middleware: Optional[Callable] = None

    @property
    def is_opened(self) -> bool:
        """Session status."""
        return self._is_opened

    async def startup(self):
        """Open aiohttp session, call startup callbacks."""
        self._session = aiohttp.ClientSession()
        self._is_opened = True
        if self._on_startup:
            if is_async_callable(self._on_startup):
                await self._on_startup()
            else:
                self._on_startup()

    async def shutdown(self):
        """Close aiohttp session, call shutdown callbacks."""
        await self._session.close()
        self._session = None
        self._is_opened = False
        if self._on_shutdown:
            if is_async_callable(self._on_shutdown):
                await self._on_shutdown()
            else:
                self._on_shutdown()

    def _call_factory(self, method: str) -> Callable:
        """Create call function for request."""
        method = method.lower()

        @asynccontextmanager
        async def call(request: ClientRequest):
            if method in ('get', 'post', 'put', 'delete'):
                url = concat_url(self.url, request.route)
                async with getattr(self._session, method)(
                    url,
                    params=request.params,
                    headers=request.headers,
                    json=request.json
                ) as response:
                    yield response
            else:
                raise ValueError(f'Unknown method {method}')

        return call

    @asynccontextmanager
    async def request(
        self,
        route: str,
        method: str = 'GET',
        params: Optional[dict[str, any]] = None,
        headers: Optional[dict[str, str]] = None,
        json: Optional[dict[str, any]] = None
    ) -> aiohttp.ClientResponse:
        """Send async request to given route."""
        request = ClientRequest(
            route=route,
            params=params,
            headers=headers,
            json=json
        )
        call = self._call_factory(method)
        if self._middleware:
            async with self._middleware(request, call) as response:
                yield response
        else:
            async with call(request) as response:
                yield response

    async def request_no_response(
        self,
        route: str,
        method: str = 'GET',
        params: Optional[dict[str, any]] = None,
        headers: Optional[dict[str, str]] = None,
        json: Optional[dict[str, any]] = None
    ):
        """Send async request to given route without response."""
        async with self.request(route=route, method=method, params=params,
                                headers=headers, json=json):
            pass

    def on_startup(self, func: Callable):
        """Decorator for setting startup callback."""
        self._on_startup = func
        return func

    def on_shutdown(self, func: Callable):
        """Decorator for setting shutdown callback."""
        self._on_shutdown = func
        return func

    def middleware(self, func: Callable):
        """
        Decorator for setting middleware.

        Middleware is an async context manager function with two arguments:
        - request (ClientRequest)
        - call (Callable[[ClientRequest], Awaitable[RequsetContextManager]])

        Middleware can be used for request modification.

        Usage:
        ```python
        @session.middleware
        @asynccontextmanager
        async def middleware(request: ClientRequest, call: Callable):
            requset.headers['X-Auth'] = '123'
            async with call(request) as response:
                if response.status == 401:
                    raise UnauthorizedError()
                yield response
        ```
        """
        self._middleware = func
        return func
