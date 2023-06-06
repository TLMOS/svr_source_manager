from typing import Optional, Callable
from functools import partial
from contextlib import asynccontextmanager

import requests
import aiohttp


def concat_url(url: str, route: str) -> str:
    """Concatenate url and route."""
    if url[-1] != '/':
        url += '/'
    route = route.strip('/')
    return url + route


class ClientSession:
    """
    Requests wrapper with middleware support.

    Usage:
    ```python
    session = ClientSession('http://example.com')

    @session.middleware
    def middleware(call: Callable, route: str, **kwargs):
        if 'X-Auth' not in kwargs['headers']:
            kwargs['headers']['X-Auth'] = '123'
        response = call(route, **kwargs)
        if response.status_code == 401:
            raise UnauthorizedError()
        return response

    def ping():
        url = 'ping'
        response = session.request('GET', url)
        print(response.text())
    """

    def __init__(self, base_url: str):
        self.base_url = base_url
        self._middleware: Optional[Callable] = None

    def middleware(self, func: Callable):
        """Decorator to add middleware."""
        self._middleware = func
        return func

    def _call_factory(self, method: str):
        """Create call function with middleware."""
        call = partial(requests.request, method)
        if self._middleware:
            call = partial(self._middleware, call)
        return call

    def request(self, method: str, route: str, **kwargs) -> requests.Response:
        """Make request and return response."""
        url = concat_url(self.base_url, route)
        call = self._call_factory(method)
        return call(url, **kwargs)


class AsyncClientSession:
    """
    Requests wrapper with middleware support.

    Usage:
    ```python
    session = ClientSession('http://example.com')
    session.open()

    @session.middleware
    @asynccontextmanager
    async def middleware(call: Callable, route: str, **kwargs):
        if 'X-Auth' not in kwargs['headers']:
            kwargs['headers']['X-Auth'] = '123'
        async with call(route, **kwargs) as response:
            if response.status == 401:
                raise UnauthorizedError()
            yield response

    async def ping():
        url = 'ping'
        async with session.request('GET', url) as response:
            text = await response.text()
            print(text)
    """

    def __init__(self, base_url: str):
        self.base_url = base_url
        self._middleware: Optional[Callable] = None

    def open(self):
        """Open aiohttp session."""
        self._session = aiohttp.ClientSession()

    async def close(self):
        """Safely close aiohttp session."""
        try:
            await self._session.close()
        except Exception:
            pass  # Session is already closed
        self._session = None

    def middleware(self, func: Callable):
        """Decorator to add middleware."""
        self._middleware = func
        return func

    def _call_factory(self, method: str):
        """Create call function with middleware."""
        method = method.lower()
        if method in ('get', 'post', 'put', 'delete'):
            call = getattr(self._session, method)
            if self._middleware:
                return partial(self._middleware, call)
        else:
            raise ValueError(f'Unknown method {method}')

    @asynccontextmanager
    async def request(self, method: str, route: str,
                      **kwargs) -> aiohttp.ClientResponse:
        """Make async request and yield response."""
        url = concat_url(self.base_url, route)
        call = self._call_factory(method)
        async with call(url, **kwargs) as response:
            yield response
