import uuid

from fastapi import APIRouter, HTTPException

from app import crud, security
from app.database import SessionDep

router = APIRouter(
    prefix="/security",
    tags=["Securirty"],
)


@router.get(
    '/verify_web_ui_password',
    summary="Verify Web-UI password"
)
async def verify_web_ui_password(session: SessionDep, password: str) -> bool:
    """
    Verify Web-UI password.

    Parameters:
    - password (str): Web-UI user password

    Raises:
    - HTTPException 500: If password not found in the database

    Returns:
    - bool: True if password is correct, False otherwise
    """
    password_db = await crud.secrets.read_by_name(session, 'web_ui_password')
    if password_db is None:
        raise HTTPException(
            status_code=500,
            detail="Password not found in the database."
        )
    return security.verify_secret(password, password_db.value)


@router.put(
    '/update_web_ui_password',
    summary="Update Web-UI password"
)
async def update_web_ui_password(session: SessionDep, password: str):
    """
    Update Web-UI password.

    Parameters:
    - password (str): New Web-UI user password
    """
    password_hash = security.get_secret_hash(password)
    await crud.secrets.update_value(session, 'web_ui_password', password_hash)


@router.put(
    '/update_token',
    summary="Update API token"
)
async def update_token(session: SessionDep):
    """
    Generate new API token. Old token will be invalidated.

    Returns:
    - dict: New API token
    """
    token = str(uuid.uuid4())
    token_hash = security.get_secret_hash(token)
    await crud.secrets.update_value(session, 'api_token', token_hash)
    return {'token': token}


@router.delete(
    '/invalidate_token',
    summary="Invalidate API token"
)
async def invalidate_token(session: SessionDep):
    """
    Invalidate API token.

    Returns:
    - dict: Empty dict
    """
    await crud.secrets.update_value(session, 'api_token', None)
