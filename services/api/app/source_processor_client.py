import requests

from fastapi import HTTPException

from app.config import settings
from app.models import Source
from app import schemas


def base_reqest(method: str,
                route: str,
                params: dict = {},
                json: str | None = None,
                ) -> requests.Response:
    """
    Send request to source processor.

    Args:
        method: HTTP method.
        route: Route to send request to.
        params: Params to send with request.
    """
    response = requests.request(
        method=method,
        url=f'{settings.source_processor_url}/{route}',
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


def add(source: Source):
    source_schema = schemas.Source.from_orm(source)
    base_reqest('POST', 'add', json=source_schema.dict())


def remove(source_id: int):
    base_reqest('DELETE', 'remove', params={
        'source_id': source_id
    })


def get_frame(source_id: int) -> bytes:
    return base_reqest('GET', 'get_frame', params={
        'source_id': source_id
    }).content
