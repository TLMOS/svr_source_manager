from fastapi import HTTPException

from common.config import settings
from common.schemas import Source, VideoChunk, VideoChunkCreate
from common.constants import SourceStatus
from common.clients.http import ClientSession
from common.utils.fastapi import get_error_msg


session = ClientSession(settings.api.url)


@session.middleware
def middleware(call, url, **kwargs):
    if 'headers' not in kwargs:
        kwargs['headers'] = {}
    kwargs['headers']['X-Is-Internal'] = '1'
    kwargs['headers']['Authorization'] = 'Bearer source_manager'
    response = call(url, **kwargs)
    if response.status_code >= 400:
        msg = get_error_msg(response)
        detail = f'Got `{msg}` while sending request to source manager'
        raise HTTPException(response.status_code, detail)
    return response


def get_all_sources(status: SourceStatus) -> list[Source]:
    url = '/sources/get/all'
    params = {'status': status.value}
    response = session.request('GET', url, params=params)
    sources = [Source(**source) for source in response.json()]
    return sources


def update_source_status(id: int, status: SourceStatus,
                         status_msg: str):
    url = '/sources/update_status'
    params = {
        'id': id,
        'status': status.value,
        'status_msg': status_msg,
    }
    session.request('PUT', url, params=params)


def create_video_chunk(chunk: VideoChunkCreate) -> VideoChunk:
    url = '/videos/chunks/create'
    response = session.request('POST', url, json=chunk.dict())
    return VideoChunk(**response.json())
