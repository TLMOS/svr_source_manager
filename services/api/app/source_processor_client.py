import aiohttp
from fastapi import HTTPException

from common import schemas
from common.http_client import AsyncClientSession
from app.config import settings
from app import models


session = AsyncClientSession(settings.source_processor_url)


@session.on_response
async def on_response(resp: aiohttp.ClientResponse):
    if resp.status != 200:
        msg = 'Unparsable response'
        if 'Content-Type' in resp.headers:
            if resp.headers['Content-Type'] == 'application/json':
                msg = await resp.json()
            elif resp.headers['Content-Type'] == 'text/html; charset=utf-8':
                msg = await resp.text()
            elif resp.headers['Content-Type'] == 'text/plain; charset=utf-8':
                msg = await resp.text()
        if 'detail' in msg:
            msg = msg['detail']
        if isinstance(msg, list):
            msg = msg[0]
        if 'msg' in msg:
            msg = msg['msg']
        detail = f'Got "{msg}" while sending request to source processor'
        raise HTTPException(resp.status, detail)


async def add(db_source: models.Source) -> None:
    """
    Add source to the processing list.

    Parameters:
    - db_source (models.Source): source to add
    """
    source = schemas.Source.from_orm(db_source)
    async with session.post('add', json=source.dict()):
        pass


async def remove(source_id: int) -> None:
    """
    Remove source from the processing list.

    Parameters:
    - source_id (int): source id
    """
    async with session.delete('remove', params={'source_id': source_id}):
        pass
