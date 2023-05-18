
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Secret


async def read_by_name(session: AsyncSession, name: str) -> Secret:
    """Read secret from the database by name."""
    statement = select(Secret).filter(Secret.name == name)
    result = await session.execute(statement)
    return result.scalars().first()


async def update_value(session: AsyncSession, name: str, value: str) -> Secret:
    """Update secret value."""
    db_secret = await read_by_name(session, name)
    db_secret.value = value
    await session.commit()
    return db_secret
