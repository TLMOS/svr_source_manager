from fastapi import Depends, Header, HTTPException
from fastapi.security import HTTPBearer

from common.credentials import credentials_loader
from app.security import secrets


api_key_scheme = HTTPBearer()


def requires_auth(
    api_key: str = Depends(api_key_scheme),
    x_is_internal: str = Header(0)
):
    if x_is_internal == '1':
        # Skip authentication for internal requests, e.g. from the
        # source processor. External requests are stripped of this header
        # by the nginx reverse proxy.
        return
    api_key = api_key.credentials
    if not credentials_loader.is_registered():
        raise HTTPException(
            status_code=400,
            detail='Source manager is not registered'
        )
    api_key_hash = credentials_loader.credentials.api_key_hash
    if not secrets.verify(api_key, api_key_hash):
        raise HTTPException(
            status_code=401,
            detail='Invalid API key',
            headers={'WWW-Authenticate': 'Bearer'},
        )
