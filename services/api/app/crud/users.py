from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User
from app import schemas


async def create(session: AsyncSession,
                 user_schema: schemas.UserCreate) -> User:
    """Create user in the database."""
    user = User(**user_schema.dict())
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


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
    user = await read(session, id)
    await session.delete(user)
    await session.commit()
    return user
