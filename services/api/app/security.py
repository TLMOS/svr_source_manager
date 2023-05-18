from typing import Annotated

import bcrypt
from fastapi import HTTPException, Header, Depends

from app import crud
from app.database import SessionDep


def verify_secret(plain_secret: str, hashed_secret: str) -> bool:
    """
    Verify a secret against a hash using slow hashing.

    Args:
    - plain_secret (str): Plain secret
    - hashed_secret (str): Secret hashed with bcrypt

    Returns:
    - bool: True if secret is correct, False otherwise
    """
    return bcrypt.checkpw(plain_secret.encode(), hashed_secret.encode())


def get_secret_hash(secret) -> str:
    """
    Get a hash of a secret using bcrypt.

    Args:
    - secret (str): Secret to hash

    Returns:
    - str: Hashed secret
    """
    return bcrypt.hashpw(secret.encode(), bcrypt.gensalt()).decode()


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
    scheme, token_plain = www_authenticate.split(' ')
    if scheme.lower() != 'bearer':
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication scheme."
        )
    token_db = await crud.secrets.read_by_name(session, 'api_token')
    if token_db is None:
        raise HTTPException(
            status_code=500,
            detail="API token not found in the database."
        )
    if not verify_secret(token_plain, token_db.value):
        raise HTTPException(
            status_code=401,
            detail="Invalid token."
        )


# FastAPI dependency for routes exposed to the public through
# the nginx reverse proxy server, requiring a valid API token
# in the Authorization header
ExposedDep = Depends(require_token_auth)
