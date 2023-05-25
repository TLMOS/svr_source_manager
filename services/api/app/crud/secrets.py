from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Secret


async def read(db: AsyncSession, name: str) -> Optional[str]:
    """Read secret from the database by name."""
    statement = select(Secret).filter(Secret.name == name)
    result = await db.execute(statement)
    db_secret = result.scalars().first()
    if db_secret:
        return db_secret.value
    else:
        return None


async def read_all_encrypted(db: AsyncSession) -> list[Secret]:
    """Read all encrypted secrets from the database."""
    statement = select(Secret).filter(Secret.encrypted)
    result = await db.execute(statement)
    return result.scalars().all()


async def update(db: AsyncSession, name: str, value: str,
                 encrypted: bool = False):
    """Update secret value. If secret does not exist, create it."""
    statement = select(Secret).filter(Secret.name == name)
    result = await db.execute(statement)
    db_secret = result.scalars().first()
    if db_secret:
        db_secret.value = value
    else:
        db_secret = Secret(name=name, value=value, encrypted=encrypted)
        db.add(db_secret)
    await db.commit()
