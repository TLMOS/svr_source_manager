"""Pydantic schemas for the data server."""

from typing import Optional
from pydantic import BaseModel
from common.constants import SourceStatus


class SourceBase(BaseModel):
    name: str
    url: str


class SourceCreate(SourceBase):
    pass


class Source(SourceBase):
    id: int
    status_code: SourceStatus
    status_msg: Optional[str] = None

    class Config:
        orm_mode = True
        schema_extra = {
            'example': {
                'id': 1,
                'name': 'Parking lot',
                'url': 'http://example.com/video.mjpg',
                'status_code': 0,
                'status_msg': None
            }
        }


class VideoChunkBase(BaseModel):
    source_id: int
    file_path: str
    start_time: float
    end_time: float


class VideoChunkCreate(VideoChunkBase):
    pass


class VideoChunk(VideoChunkBase):
    id: int

    class Config:
        orm_mode = True
        schema_extra = {
            'example': {
                'id': 1,
                'source_id': 1,
                'file_path': '/path/to/chunk.mp4',
                'start_time': 0.0,
                'end_time': 10.0
            }
        }
