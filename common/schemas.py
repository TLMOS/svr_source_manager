"""Pydantic schemas for the data server."""

from typing import Optional

from pydantic import (
    BaseModel,
    PositiveInt,
    PositiveFloat,
    FilePath,
    FileUrl,
    HttpUrl
)

from common.constants import SourceStatus


class SourceBase(BaseModel):
    name: str
    url: FileUrl | HttpUrl


class SourceCreate(SourceBase):
    pass


class Source(SourceBase):
    id: PositiveInt
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
    source_id: PositiveInt
    file_path: FilePath
    start_time: PositiveFloat
    end_time: PositiveFloat
    farme_count: PositiveInt


class VideoChunkCreate(VideoChunkBase):
    pass


class VideoChunk(VideoChunkBase):
    id: PositiveInt

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
