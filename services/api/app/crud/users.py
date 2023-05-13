from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from common import schemas
from app.models import User


async def create(session: AsyncSession, user: schemas.UserCreate) -> User:
    """Create user in the database."""
    db_user = User(**user.dict())
    session.add(db_user)
    await session.commit()
    await session.refresh(db_user)
    return db_user


async def read(session: AsyncSession, id: int) -> User:
    """Get user by id."""
    result = await session.execute(select(User).filter(User.id == id))
    return result.scalars().first()


async def read_all(session: AsyncSession) -> list[User]:
    """Get all users."""
    result = await session.execute(select(User))
    return result.scalars().all()


async def read_by_name(session: AsyncSession, name: str) -> User:
    """Get user by name."""
    result = await session.execute(select(User).filter(User.name == name))
    return result.scalars().first()


async def delete(session: AsyncSession, id: int) -> User:
    """Delete user from the database."""
    db_user = await read(session, id)
    await session.delete(db_user)
    await session.commit()
    return db_user
