from typing import Callable
from contextlib import asynccontextmanager

from fastapi import HTTPException

from common import schemas
from common.http_client import AsyncClientSession, ClientRequest
from common.config import settings
from app import models


session = AsyncClientSession(settings.source_processor.url)


@session.middleware
@asynccontextmanager
async def middleware(request: ClientRequest, call: Callable):
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
            detail = f'Got `{msg}` while sending request to source processor'
            raise HTTPException(response.status, detail)
        yield response


async def add(db_source: models.Source):
    """
    Add source to the processing list.

    Parameters:
    - db_source (models.Source): source to add
    """
    url = 'add'
    source = schemas.Source.from_orm(db_source)
    await session.request_no_response(url, 'POST', json=source.dict())


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
    await session.request_no_response(url, 'DELETE', params=params)


async def rabbitmq_startup(username: str, password: str,
                           sm_name: str):
    """
    Start RabbitMQ session.

    Parameters:
    - username (str): RabbitMQ username
    - password (str): RabbitMQ password
    """
    url = 'rabbitmq/startup'
    params = {
        'username': username,
        'password': password,
        'sm_name': sm_name,
    }
    await session.request_no_response(url, 'POST', params=params)


async def rabbitmq_shutdown():
    """Stop RabbitMQ session"""
    url = 'rabbitmq/shutdown'
    await session.request_no_response(url, 'POST')


async def rabbitmq_is_opened() -> bool:
    """Check if RabbitMQ session is opened"""
    url = 'rabbitmq/is_opened'
    async with session.request(url, 'GET') as response:
        return await response.json()
