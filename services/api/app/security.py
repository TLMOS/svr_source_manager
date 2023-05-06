import bcrypt
from typing import Annotated

from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi import Depends, HTTPException, status

from app import crud
from app.dependencies import SessionDep
from app.models import User


# Password hashing and verification


def get_password_hash(password: str) -> str:
    """Get password hash."""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, password_hash: str) -> bool:
    """Verify password."""
    return bcrypt.checkpw(password.encode(), password_hash.encode())


# Authentication FastAPI dependencies


security = HTTPBasic()
CredentialsDep = Annotated[HTTPBasicCredentials, Depends(security)]
forget_list = []


def forget(username: str):
    """Add username to forget list."""
    forget_list.append(username)


async def requires_auth(credentials: CredentialsDep,
                        session: SessionDep) -> tuple[User, AsyncSession]:
    """Check if user is authenticated."""
    verified = True
    user = await crud.users.read_by_name(session, credentials.username)
    if credentials.username in forget_list:
        forget_list.remove(credentials.username)
        verified = False
    elif not user:
        verified = False
    elif not verify_password(credentials.password, user.password):
        verified = False
    if not verified:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return user, session


async def requires_admin(credentials: CredentialsDep,
                         session: SessionDep) -> AsyncSession:
    """Check if user is admin."""
    verified = True
    user = await crud.users.read_by_name(session, credentials.username)
    if credentials.username in forget_list:
        forget_list.remove(credentials.username)
        verified = False
    elif not user:
        verified = False
    elif not verify_password(credentials.password, user.password):
        verified = False
    if not verified:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    return session


RequiresAuthDep = Annotated[tuple[User, AsyncSession], Depends(requires_auth)]
RequiresAdminDep = Annotated[AsyncSession, Depends(requires_admin)]
