import requests

from fastapi import HTTPException

from common.constants import SourceStatus
from common.schemas import VideoChunkCreate, Source
from app.config import settings


def base_reqest(method: str,
                route: str,
                params: dict = {},
                json: str | None = None
                ) -> requests.Response:
    """
    Send request to core api.

    Args:
        method: HTTP method.
        route: Route to send request to.
        params: Params to send with request.
    """
    url = f'{settings.api_url}/{route}'
    try:
        response = requests.request(method, url, params=params, json=json)
    except requests.exceptions.ConnectionError as e:
        raise HTTPException(status_code=404, detail=e.strerror)
    if response.status_code != 200:
        raise HTTPException(
            response.status_code,
            response.json()['detail'],
            response.headers
        )
    return response


def get_all_active_sources() -> list[Source]:
    response = base_reqest('GET', 'sources/get/all', params={
        'status': SourceStatus.ACTIVE.value
    })
    return [Source(**source) for source in response.json()]


def update_source_status(id: int, status: SourceStatus,
                         status_msg: str | None = None):
    base_reqest('PUT', 'sources/update_status', params={
        'id': id,
        'status': status.value,
        'status_msg': status_msg
    })


def create_video_chunk(chunk: VideoChunkCreate):
    base_reqest('POST', 'videos/chunks/create', json=chunk.dict())
