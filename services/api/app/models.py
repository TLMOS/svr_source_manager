from sqlalchemy import Column, Integer, Float, Boolean, String, ForeignKey
from sqlalchemy.orm import relationship

from common.constants import SourceStatus
from .database import Base


class Secret(Base):
    __tablename__ = 'secret'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    value = Column(String, nullable=False)
    encrypted = Column(Boolean, default=False, nullable=False)


class Source(Base):
    __tablename__ = 'source'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    url = Column(String)
    status_code = Column(Integer, default=SourceStatus.PAUSED, nullable=False)
    status_msg = Column(String, nullable=True)

    chunks = relationship('VideoChunk', back_populates='source',
                          cascade='all, delete')


class VideoChunk(Base):
    __tablename__ = 'video_chunk'

    id = Column(Integer, primary_key=True, index=True)
    file_path = Column(String, unique=True, nullable=False)
    start_time = Column(Float, nullable=False)
    end_time = Column(Float, nullable=False)
    n_frames = Column(Integer, nullable=False)
    source_id = Column(Integer, ForeignKey('source.id'), nullable=False)

    source = relationship('Source', back_populates='chunks')
