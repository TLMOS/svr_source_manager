from enum import IntEnum

from pydantic import BaseModel


class SourceStatus(IntEnum):
    ACTIVE = 0
    PAUSED = 1
    FINISHED = 2
    ERROR = 3


class VideoChunkCreate(BaseModel):
    source_id: int
    file_path: str
    start_time: float
    end_time: float


class Source(BaseModel):
    id: int
    name: str
    url: str
    status_code: SourceStatus
    status_msg: str | None = None
    user_id: int

    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "id": 1,
                "name": "Parking lot",
                "url": "http://example.com/video.mjpg",
                "status_code": 0,
                "status_msg": None
            }
        }
