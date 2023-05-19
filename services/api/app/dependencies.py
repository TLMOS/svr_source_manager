from typing import Annotated

from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends, HTTPException, Header

from app import crud, security
from app.database import async_session_factory


async def get_database_session() -> AsyncSession:
    """FastAPI dependency to get a database session"""
    async with async_session_factory() as session:
        yield session


SessionDep = Annotated[AsyncSession, Depends(get_database_session)]


async def require_token_auth(session: SessionDep,
                             www_authenticate: str = Header(...)) -> None:
    """
    Raise an exception if the request does not contain a valid token.

    Args:
    - www_authenticate (str): Authorization header

    Raises:
    - HTTPException 401: If the request does not contain a valid token
    - HTTPException 500: If the API token is not found in the database
    """
    if len(www_authenticate.split(' ')) != 2:
        raise HTTPException(
            status_code=401,
            detail='Invalid authorization header.'
        )
    scheme, token_plain = www_authenticate.split(' ')
    if scheme.lower() != 'bearer':
        raise HTTPException(
            status_code=401,
            detail='Invalid authentication scheme.'
        )
    token_hash = await crud.secrets.read(session, 'api_token')
    if token_hash is None:
        raise HTTPException(
            status_code=500,
            detail='API token not found in the database.'
        )
    if not security.verify_secret(token_plain, token_hash):
        raise HTTPException(
            status_code=401,
            detail='Invalid token.'
        )


TokenAuthDep = Depends(require_token_auth)
