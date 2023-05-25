from typing import Annotated

from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends
from app.database import async_session_factory


async def get_database_session() -> AsyncSession:
    """FastAPI dependency to get a database session"""
    async with async_session_factory() as session:
        yield session


DatabaseDepends = Annotated[AsyncSession, Depends(get_database_session)]
