import aiohttp
from fastapi import HTTPException

from common.http_client import AsyncClientSession
from common.constants import SourceStatus
from common.schemas import VideoChunkCreate, Source
from app.config import settings


session = AsyncClientSession(settings.api_url)


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
        detail = f'Got "{msg}" while sending request to api service \
            with url {resp.url}'
        raise HTTPException(resp.status, detail)


async def get_all_active_sources() -> list[Source]:
    """
    Get all active sources.

    Returns:
    - list[Source]: list of active sources
    """
    params = {'status': SourceStatus.ACTIVE.value}
    async with session.get('sources/get/all', params=params) as response:
        return [Source(**source) for source in await response.json()]


async def update_source_status(id: int, status: SourceStatus,
                               status_msg: str | None = None):
    """
    Update source status.

    Parameters:
    - id (int): source id
    - status (SourceStatus): new source status
    - status_msg (str | None): status message
    """
    params = {'id': id, 'status': status.value, 'status_msg': status_msg}
    async with session.put('sources/update_status', params=params):
        pass


async def create_video_chunk(chunk: VideoChunkCreate):
    """
    Create video chunk.

    Parameters:
    - chunk (VideoChunkCreate): video chunk
    """
    async with session.post('videos/chunks/create', json=chunk.dict()):
        pass
