from typing import Optional, Callable
from contextlib import asynccontextmanager

from fastapi import HTTPException

from common.http_client import AsyncClientSession, ClientRequest
from common.constants import SourceStatus
from common.schemas import VideoChunkCreate, Source
from common.config import settings


session = AsyncClientSession(settings.api.url)


@session.middleware
@asynccontextmanager
async def middleware(request: ClientRequest, call: Callable):
    request.headers['X-Is-Local'] = 'true'  # Do not require token auth locally
    request.headers['Authorization'] = 'Bearer None'  # OAuth2 plug for FastAPI
    async with call(request) as response:
        if response.status != 200:
            msg = 'Unparsable response'
            content_type = response.headers.get('Content-Type', None)
            if 'Content-Type' in response.headers:
                if content_type == 'application/json':
                    msg = await response.json()
                elif content_type == 'text/html; charset=utf-8':
                    msg = await response.text()
                elif content_type == 'text/plain; charset=utf-8':
                    msg = await response.text()
            if isinstance(msg, dict) and 'detail' in msg:
                msg = msg['detail']
            if isinstance(msg, list):
                msg = msg[0]
            if isinstance(msg, dict) and 'msg' in msg:
                msg = msg['msg']
            detail = f'Got `{msg}` while sending request to api service'
            raise HTTPException(response.status, detail)
        yield response


async def get_all_active_sources() -> list[Source]:
    """
    Get all active sources.

    Returns:
    - list[Source]: list of active sources
    """
    url = 'sources/get/all'
    params = {
        'status': SourceStatus.ACTIVE.value
    }
    async with session.request(url, 'GET', params=params) as response:
        sources = await response.json()
        return [Source(**source) for source in sources]


async def update_source_status(id: int, status: SourceStatus,
                               status_msg: Optional[str] = None):
    """
    Update source status.

    Parameters:
    - id (int): source id
    - status (SourceStatus): new source status
    - status_msg (Optional[str]): new source status message
    """
    url = 'sources/update_status'
    params = {
        'id': id,
        'status': status.value,
        'status_msg': status_msg
    }
    await session.request_no_response(url, 'PUT', params=params)


async def create_video_chunk(chunk: VideoChunkCreate):
    """
    Create video chunk.

    Parameters:
    - chunk (VideoChunkCreate): video chunk
    """
    url = 'videos/chunks/create'
    await session.request_no_response(url, 'POST', json=chunk.dict())
