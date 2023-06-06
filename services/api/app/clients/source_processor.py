from typing import Callable
from contextlib import asynccontextmanager

from fastapi import HTTPException

from common import schemas
from common.clients.http import AsyncClientSession
from common.config import settings
from common.database import models
from common.utils.fastapi import get_error_msg_async


session = AsyncClientSession(settings.source_processor.url)


@session.middleware
@asynccontextmanager
async def middleware(call: Callable, url: str, **kwargs):
    async with call(url, **kwargs) as response:
        if response.status >= 400:
            msg = await get_error_msg_async(response)
            detail = f'Got `{msg}` while sending request to source processor'
            raise HTTPException(response.status, detail)
        yield response


async def restart():
    """Restart source processor."""
    url = 'restart'
    async with session.request('POST', url):
        pass


async def add(db_source: models.Source):
    """
    Add source to the processing list.

    Parameters:
    - db_source (models.Source): source to add
    """
    url = 'add'
    source = schemas.Source.from_orm(db_source)
    async with session.request('POST', url, json=source.dict()):
        pass


async def remove(source_id: int):
    """
    Remove source from the processing list.

    Parameters:
    - source_id (int): source id
    """
    url = 'remove'
    params = {
        'source_id': source_id
    }
    async with session.request('DELETE', url, params=params):
        pass
