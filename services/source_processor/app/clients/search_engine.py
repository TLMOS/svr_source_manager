from fastapi import HTTPException

from common.config import settings
from common.credentials import credentials_loader, RabbitMQCredentials
from common.clients.http import ClientSession
from common.utils.fastapi import get_error_msg


session = ClientSession(settings.search_engine.url)


@session.middleware
def middleware(call, url, **kwargs):
    if 'headers' not in kwargs:
        kwargs['headers'] = {}
    auth_token = credentials_loader.credentials.search_engine.auth_token
    kwargs['headers']['Authorization'] = f'Bearer {auth_token}'
    response = call(url, **kwargs)
    if response.status_code >= 400:
        msg = get_error_msg(response)
        detail = f'Got `{msg}` while sending request to search engine'
        raise HTTPException(response.status_code, detail)
    return response


def get_rabbitmq_credentials() -> RabbitMQCredentials:
    url = 'rabbitmq/credentials'
    response = session.request('GET', url)
    return RabbitMQCredentials(**response.json())
