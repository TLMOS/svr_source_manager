from typing import Annotated
from pathlib import Path
import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends

from app.config import settings
from app.database import async_session_factory
from app.video_processing import SourceProcessor
from app import crud


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


# Source processor dependency


source_processor = None


async def get_source_processor() -> SourceProcessor:
    """FastAPI dependency to get a source processor"""
    global source_processor
    if source_processor is None:
        source_processor = SourceProcessor()
        async with async_session_factory() as session:
            active_sources = await crud.sources.read_active(session)
            for source in active_sources:
                source_processor.add(source)
    yield source_processor


SourceProcessorDep = Annotated[SourceProcessor, Depends(get_source_processor)]
