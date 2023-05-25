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
    source = schemas.Source.from_orm(db_source)
    await session.request_no_response('add', 'POST', json=source.dict())


async def remove(source_id: int):
    """
    Remove source from the processing list.

    Parameters:
    - source_id (int): source id
    """
    params = {
        'source_id': source_id
    }
    await session.request_no_response('remove', 'DELETE',
                                      params=params)


async def rabbitmq_startup(username: str, password: str):
    """
    Start RabbitMQ session.

    Parameters:
    - username (str): RabbitMQ username
    - password (str): RabbitMQ password
    """
    params = {
        'username': username,
        'password': password
    }
    await session.request_no_response('rabbitmq/startup', 'POST',
                                      params=params)


async def rabbitmq_shutdown():
    """Stop RabbitMQ session"""
    await session.request_no_response('rabbitmq/shutdown', 'POST')


async def rabbitmq_is_opened() -> bool:
    """Check if RabbitMQ session is opened"""
    async with session.request('rabbitmq/is_opened', 'GET') as resp:
        return await resp.json()
