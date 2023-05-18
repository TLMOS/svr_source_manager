from urllib.error import HTTPError

import requests
from requests.exceptions import JSONDecodeError

from common.http_client import ClientSession
from app.config import settings


session = ClientSession(settings.api_url)


@session.on_response
def on_response(resp: requests.Response):
    if resp.status_code != 200:
        try:
            msg = resp.json()
            if 'detail' in msg:
                msg = msg['detail']
            if isinstance(msg, list):
                msg = msg[0]
            if 'msg' in msg:
                msg = msg['msg']
        except JSONDecodeError:
            msg = 'Unparsable response'
        detail = f'Got "{msg}" while sending request to api service'
        raise HTTPError(
            url=resp.url,
            code=resp.status_code,
            msg=detail,
            hdrs=resp.headers,
            fp=None
        )
