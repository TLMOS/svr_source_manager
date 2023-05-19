
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Secret


async def read(session: AsyncSession, name: str) -> str | None:
    """Read secret from the database by name."""
    statement = select(Secret).filter(Secret.name == name)
    result = await session.execute(statement)
    db_secret = result.scalars().first()
    if db_secret:
        return db_secret.value
    else:
        return None


async def update(session: AsyncSession, name: str, value: str):
    """Update secret value. If secret does not exist, create it."""
    statement = select(Secret).filter(Secret.name == name)
    result = await session.execute(statement)
    db_secret = result.scalars().first()
    if db_secret:
        db_secret.value = value
    else:
        db_secret = Secret(name=name, value=value)
        session.add(db_secret)
    await session.commit()
