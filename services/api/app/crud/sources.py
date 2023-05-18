
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from common import schemas
from common.constants import SourceStatus
from app.models import Source


async def create(session: AsyncSession,
                 source: schemas.SourceCreate) -> Source:
    """Create source in the database."""
    db_source = Source(**source.dict())
    session.add(db_source)
    await session.commit()
    await session.refresh(db_source)
    return db_source


async def read(session: AsyncSession, id: int) -> Source:
    """Read source from the database."""
    statement = select(Source).filter(Source.id == id)
    result = await session.execute(statement)
    return result.scalars().first()


async def read_all(session: AsyncSession,
                   status: SourceStatus | None = None) -> list[Source]:
    """Read all sources from the database."""
    statement = select(Source)
    if status is not None:
        statement = statement.filter(Source.status_code == status)
    result = await session.execute(statement)
    return result.scalars().all()


async def update_status(session: AsyncSession, id: int, status: SourceStatus,
                        status_msg: str = None) -> Source:
    """Update source status and status message."""
    db_source = await read(session, id)
    db_source.status_code = status.value
    db_source.status_msg = status_msg
    await session.commit()
    return db_source


async def delete(session: AsyncSession, id: int) -> Source:
    """Delete source from the database."""
    db_source = await read(session, id)
    await session.delete(db_source)
    await session.commit()
    return db_source
