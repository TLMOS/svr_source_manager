from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker

from common.config import settings


engine = create_async_engine(settings.postgres.url, echo=False)
Base = declarative_base()
async_session_factory = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)
