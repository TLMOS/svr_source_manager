from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from common import schemas
from app.models import VideoChunk, Source


def filter_by_user(statement, user_id: int | None) -> None:
    """Filter video chunks by user."""
    if user_id is not None:
        statement = statement.join(VideoChunk.source).filter(
            Source.user_id == user_id
        )
    return statement


async def create(session: AsyncSession,
                 chunk: schemas.VideoChunkCreate) -> VideoChunk:
    """Create video chunk in the database."""
    db_chunk = VideoChunk(**chunk.dict())
    session.add(db_chunk)
    await session.commit()
    await session.refresh(db_chunk)
    return db_chunk


async def read(session: AsyncSession, id: int,
               user_id: int | None = None) -> VideoChunk:
    """Get video chunk by id."""
    statement = select(VideoChunk).filter(VideoChunk.id == id)
    statement = filter_by_user(statement, user_id)
    result = await session.execute(statement)
    return result.scalars().first()


async def read_all(session: AsyncSession, source_id: int,
                   user_id: int | None = None) -> list[VideoChunk]:
    """Get all video chunks of the source."""
    statement = select(VideoChunk).filter(VideoChunk.source_id == source_id)
    statement = filter_by_user(statement, user_id)
    result = await session.execute(statement)
    return result.scalars().all()


async def read_by_timestamp(session: AsyncSession, source_id: int,
                            timestamp: float, user_id: int | None = None
                            ) -> VideoChunk:
    """Get video chunk that contains the given timestamp."""
    statement = select(VideoChunk).filter(
        VideoChunk.source_id == source_id,
        VideoChunk.start_time <= timestamp,
        VideoChunk.end_time >= timestamp
    )
    statement = filter_by_user(statement, user_id)
    result = await session.execute(statement)
    return result.scalars().first()


async def read_all_in_interval(session: AsyncSession, source_id: int,
                               start_time: float, end_time: float,
                               user_id: int | None = None
                               ) -> list[VideoChunk]:
    """Get all video chunks that intersect with the given time interval."""
    statement = select(VideoChunk).filter(
        VideoChunk.source_id == source_id,
        VideoChunk.end_time >= start_time,
        VideoChunk.start_time <= end_time
    ).order_by(VideoChunk.start_time)
    statement = filter_by_user(statement, user_id)
    result = await session.execute(statement)
    return result.scalars().all()
