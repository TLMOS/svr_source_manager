from enum import IntEnum

from sqlalchemy import Column, Integer, Float, String, ForeignKey, Boolean
from sqlalchemy.orm import relationship

from .database import Base


class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    max_sources = Column(Integer, default=5, nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)

    sources = relationship('Source', back_populates='user',
                           cascade='all, delete')


class SourceStatus(IntEnum):
    ACTIVE = 0
    PAUSED = 1
    FINISHED = 2
    ERROR = 3


class Source(Base):
    __tablename__ = 'source'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    url = Column(String)
    status_code = Column(Integer, nullable=False)
    status_msg = Column(String, nullable=True)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)

    user = relationship('User', back_populates='sources')
    chunks = relationship('VideoChunk', back_populates='source',
                          cascade='all, delete')


class VideoChunk(Base):
    __tablename__ = 'video_chunk'

    id = Column(Integer, primary_key=True, index=True)
    file_path = Column(String, unique=True, nullable=False)
    start_time = Column(Float, nullable=False)
    end_time = Column(Float, nullable=False)
    source_id = Column(Integer, ForeignKey('source.id'), nullable=False)

    source = relationship('Source', back_populates='chunks')
