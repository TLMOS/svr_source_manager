import requests
import aiohttp


def get_error_msg(response: requests.Response) -> str:
    """
    Extracts error message from FastAPI error response.

    Parameters:
    - response (requests.Response): response object

    Returns:
    - str: error message
    """
    msg = 'Unparsable response'
    content_type = response.headers.get('Content-Type', None)
    if 'Content-Type' in response.headers:
        if content_type == 'application/json':
            msg = response.json()
        elif content_type == 'text/html; charset=utf-8':
            msg = response.text
        elif content_type == 'text/plain; charset=utf-8':
            msg = response.text
    if isinstance(msg, dict) and 'detail' in msg:
        msg = msg['detail']
    if isinstance(msg, list):
        msg = msg[0]
    if isinstance(msg, dict) and 'msg' in msg:
        msg = msg['msg']
    return msg


async def get_error_msg_async(response: aiohttp.ClientResponse) -> str:
    """
    Extracts error message from FastAPI error response.

    Parameters:
    - response (aiohttp.ClientResponse): response object

    Returns:
    - str: error message
    """
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
    return msg
