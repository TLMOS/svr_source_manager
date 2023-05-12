
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Source, SourceStatus


def filter_by_user(statement, user_id: int | None) -> None:
    """Filter sources by user."""
    if user_id is not None:
        statement = statement.filter(Source.user_id == user_id)
    return statement


async def create(session: AsyncSession, name: str, url: str,
                 user_id: int) -> Source:
    """Create source in the database."""
    source = Source(name=name, url=url, status_code=SourceStatus.PAUSED.value,
                    user_id=user_id)
    session.add(source)
    await session.commit()
    await session.refresh(source)
    return source


async def read(session: AsyncSession, id: int,
               user_id: int | None = None) -> Source:
    """Read source from the database."""
    statement = select(Source).filter(Source.id == id)
    statement = filter_by_user(statement, user_id)
    result = await session.execute(statement)
    return result.scalars().first()


async def read_all(session: AsyncSession,
                   user_id: int | None = None) -> list[Source]:
    """Read all sources from the database."""
    statement = select(Source)
    statement = filter_by_user(statement, user_id)
    result = await session.execute(statement)
    return result.scalars().all()


async def read_active(session: AsyncSession,
                      user_id: int | None = None) -> list[Source]:
    """Read all active sources from the database."""
    statement = select(Source).filter(
        Source.status_code == SourceStatus.ACTIVE
    )
    statement = filter_by_user(statement, user_id)
    result = await session.execute(statement)
    return result.scalars().all()


async def read_non_finished(session: AsyncSession,
                            user_id: int | None = None) -> list[Source]:
    """Read all non-finished sources from the database."""
    statement = select(Source).filter(
        Source.status_code != SourceStatus.FINISHED
    )
    statement = filter_by_user(statement, user_id)
    result = await session.execute(statement)
    return result.scalars().all()


async def update_status(session: AsyncSession, id: int, status: SourceStatus,
                        status_msg: str = None) -> Source:
    """Update source status and status message."""
    source = await read(session, id)
    source.status_code = status.value
    source.status_msg = status_msg
    await session.commit()
    return source


async def delete(session: AsyncSession, id: int) -> Source:
    """Delete source from the database."""
    source = await read(session, id)
    await session.delete(source)
    await session.commit()
    return source
