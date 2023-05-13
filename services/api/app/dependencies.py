from typing import Annotated
from pathlib import Path
import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends, Header

from app.config import settings
from app.database import async_session_factory


# Temporary file path dependency


class TmpFilePath:
    """FastAPI dependency for getting temporary file path"""

    def __init__(self, extension: str) -> Path:
        self.extension = extension

    def __call__(self) -> Path:
        path = settings.tmp_dir / f'{uuid.uuid4()}{self.extension}'
        try:
            yield path
        finally:
            if path.exists():
                path.unlink()


# Postgres session dependency


async def get_session() -> AsyncSession:
    """FastAPI dependency to get a database session"""
    async with async_session_factory() as session:
        yield session


SessionDep = Annotated[AsyncSession, Depends(get_session)]


# Extract user id and role from header dependency


async def get_user_id(x_user_id: Annotated[int | None, Header()] = None):
    """FastAPI dependency to get user id from header"""
    if x_user_id is not None:
        return int(x_user_id)


async def get_user_role(x_user_role: Annotated[int | None, Header()] = None):
    """FastAPI dependency to get user role from header"""
    if x_user_role is not None:
        return int(x_user_role)


UserIdDep = Annotated[int | None, Depends(get_user_id)]
UserRoleDep = Annotated[int | None, Depends(get_user_role)]
