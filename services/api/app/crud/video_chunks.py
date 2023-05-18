from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from common import schemas
from app.models import VideoChunk


async def create(session: AsyncSession,
                 chunk: schemas.VideoChunkCreate) -> VideoChunk:
    """Create video chunk in the database."""
    db_chunk = VideoChunk(**chunk.dict())
    session.add(db_chunk)
    await session.commit()
    await session.refresh(db_chunk)
    return db_chunk


async def read(session: AsyncSession, id: int) -> VideoChunk:
    """Get video chunk by id."""
    statement = select(VideoChunk).filter(VideoChunk.id == id)
    result = await session.execute(statement)
    return result.scalars().first()


async def read_all(session: AsyncSession, source_id: int) -> list[VideoChunk]:
    """Get all video chunks of the source."""
    statement = select(VideoChunk).filter(VideoChunk.source_id == source_id)
    result = await session.execute(statement)
    return result.scalars().all()


async def read_last(session: AsyncSession, source_id: int) -> VideoChunk:
    """Get the last video chunk of the source."""
    statement = select(VideoChunk).filter(
        VideoChunk.source_id == source_id
    ).order_by(VideoChunk.start_time.desc())
    result = await session.execute(statement)
    return result.scalars().first()


async def read_by_timestamp(session: AsyncSession, source_id: int,
                            timestamp: float) -> VideoChunk:
    """Get video chunk that contains the given timestamp."""
    statement = select(VideoChunk).filter(
        VideoChunk.source_id == source_id,
        VideoChunk.start_time <= timestamp,
        VideoChunk.end_time >= timestamp
    )
    result = await session.execute(statement)
    return result.scalars().first()


async def read_all_in_interval(session: AsyncSession, source_id: int,
                               start_time: float, end_time: float
                               ) -> list[VideoChunk]:
    """Get all video chunks that intersect with the given time interval."""
    statement = select(VideoChunk).filter(
        VideoChunk.source_id == source_id,
        VideoChunk.end_time >= start_time,
        VideoChunk.start_time <= end_time
    ).order_by(VideoChunk.start_time)
    result = await session.execute(statement)
    return result.scalars().all()
