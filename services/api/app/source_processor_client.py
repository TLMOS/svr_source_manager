import requests

from fastapi import HTTPException

from common import schemas
from app.config import settings
from app import models


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
    url = f'{settings.source_processor_url}/{route}'
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


def add(db_source: models.Source):
    source = schemas.Source.from_orm(db_source)
    base_reqest('POST', 'add', json=source.dict())


def remove(source_id: int):
    base_reqest('DELETE', 'remove', params={
        'source_id': source_id
    })


def get_frame(source_id: int) -> bytes:
    return base_reqest('GET', 'get_frame', params={
        'source_id': source_id
    }).content
