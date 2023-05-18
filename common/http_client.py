from typing import Any, Callable, Awaitable
from contextlib import asynccontextmanager

import aiohttp
import requests


class AsyncClientSession:
    """
    Async client session wrapper for aiohttp with few useful callbacks.

    Attributes:
    - url (str): base url

    Usage:
    ```python
    session = AsyncClientSession('http://example.com')

    @session.on_startup
    async def on_startup():
        print('Session started')

    @session.on_response
    async def on_response(resp: aiohttp.ClientResponse):
        if resp.status != 200:
            print('Got error response')

    def ping():
        async with session.get('ping') as resp:
            print(await resp.text())
    """

    _on_startup: Callable[[], Awaitable[None]] = None
    _on_shutdown: Callable[[], Awaitable[None]] = None
    _on_response: Callable[[aiohttp.ClientResponse], Awaitable[None]] = None

    def __init__(self, url: str):
        self.url = url
        self.__session = None

    async def startup(self):
        """Open session."""
        self.__session = aiohttp.ClientSession()
        if self._on_startup:
            await self._on_startup()

    async def shutdown(self):
        """Close session."""
        await self.__session.close()
        if self._on_shutdown:
            await self._on_shutdown()

    @asynccontextmanager
    async def get(self, route: str, **kwargs: Any) -> aiohttp.ClientResponse:
        async with self.__session.get(f'{self.url}/{route}', **kwargs) as resp:
            if self._on_response:
                await self._on_response(resp)
            yield resp

    @asynccontextmanager
    async def post(self, route: str, **kwargs: Any) -> aiohttp.ClientResponse:
        async with self.__session.post(f'{self.url}/{route}', **kwargs) as resp:
            if self._on_response:
                await self._on_response(resp)
            yield resp

    @asynccontextmanager
    async def put(self, route: str, **kwargs: Any) -> aiohttp.ClientResponse:
        async with self.__session.put(f'{self.url}/{route}', **kwargs) as resp:
            if self._on_response:
                await self._on_response(resp)
            yield resp

    @asynccontextmanager
    async def delete(self, route: str, **kwargs: Any) -> aiohttp.ClientResponse:
        async with self.__session.delete(f'{self.url}/{route}', **kwargs) as resp:
            if self._on_response:
                await self._on_response(resp)
            yield resp

    def on_startup(self, func: Callable[[], Awaitable[None]]):
        """Set startup callback."""
        self._on_startup = func
        return func

    def on_shutdown(self, func: Callable[[], Awaitable[None]]):
        """Set shutdown callback."""
        self._on_shutdown = func
        return func

    def on_response(self, func: Callable[[aiohttp.ClientResponse], Awaitable[None]]):
        """
        Set response callback.
        Called after every request.
        Can be used for error handling.
        """
        self._on_response = func
        return func


class ClientSession:
    """
    Wrapper for requests lib with few useful callbacks.

    Attributes:
    - url (str): base url

    Usage:
    ```python
    session = ClientSession('http://example.com')

    @session.on_startup
    def on_startup():
        print('Session started')

    @session.on_response
    def on_response(resp: requests.Response):
        if resp.status_code != 200:
            print('Got error response')

    def ping():
        resp = session.get('ping')
        print(resp.text)
    """

    _on_startup: Callable[[], None] = None
    _on_shutdown: Callable[[], None] = None
    _on_response: Callable[[requests.Response], None] = None

    def __init__(self, url: str):
        self.url = url

    def startup(self):
        """Run startup callback."""
        if self._on_startup:
            self._on_startup()

    def shutdown(self):
        """Run shutdown callback."""
        if self._on_shutdown:
            self._on_shutdown()

    def get(self, route: str, **kwargs: Any) -> requests.Response:
        resp = requests.get(f'{self.url}/{route}', **kwargs)
        if self._on_response:
            self._on_response(resp)
        return resp

    def post(self, route: str, **kwargs: Any) -> requests.Response:
        resp = requests.post(f'{self.url}/{route}', **kwargs)
        if self._on_response:
            self._on_response(resp)
        return resp

    def put(self, route: str, **kwargs: Any) -> requests.Response:
        resp = requests.put(f'{self.url}/{route}', **kwargs)
        if self._on_response:
            self._on_response(resp)
        return resp

    def delete(self, route: str, **kwargs: Any) -> requests.Response:
        resp = requests.delete(f'{self.url}/{route}', **kwargs)
        if self._on_response:
            self._on_response(resp)
        return resp

    def on_startup(self, func: Callable[[], None]):
        """Set startup callback."""
        self._on_startup = func
        return func

    def on_shutdown(self, func: Callable[[], None]):
        """Set shutdown callback."""
        self._on_shutdown = func
        return func

    def on_response(self, func: Callable[[requests.Response], None]):
        """
        Set response callback.
        Called after every request.
        Can be used for error handling.
        """
        self._on_response = func
        return func
