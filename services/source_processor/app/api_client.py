import requests

from fastapi import HTTPException

from app.config import settings
from app.schemas import SourceStatus, VideoChunkCreate
from app import schemas


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
    response = requests.request(
        method=method,
        url=f'{settings.api_url}/{route}',
        params=params,
        json=json
    )
    if response.status_code != 200:
        raise HTTPException(
            response.status_code,
            response.json()['detail'],
            response.headers
        )
    return response


def get_all_active_sources() -> list[schemas.Source]:
    response = base_reqest('GET', 'sources/get/all', params={
        'status': SourceStatus.ACTIVE.value
    })
    return [schemas.Source(**source) for source in response.json()]


def update_source_status(id: int, status: SourceStatus,
                         status_msg: str | None = None):
    base_reqest('PUT', 'sources/update_status', params={
        'id': id,
        'status': status.value,
        'status_msg': status_msg
    })


def create_video_chunk(chunk_schema: VideoChunkCreate):
    base_reqest('POST', 'videos/chunks/create', json=chunk_schema.dict())
