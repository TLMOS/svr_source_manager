from enum import IntEnum

from pydantic import BaseModel
from flask_login import UserMixin


class UserRole(IntEnum):
    USER = 0
    ADMIN = 1


class UserBase(BaseModel):
    name: str
    max_sources: int
    role: UserRole


class UserCreate(UserBase):
    password: str


class User(UserMixin, UserBase):
    id: int


class SourceStatus(IntEnum):
    ACTIVE = 0
    PAUSED = 1
    FINISHED = 2
    ERROR = 3


SOURCE_STATUS_TO_STR = {
    SourceStatus.ACTIVE: 'Active',
    SourceStatus.PAUSED: 'Paused',
    SourceStatus.FINISHED: 'Finished',
    SourceStatus.ERROR: 'Error',
}


class Source(BaseModel):
    id: int
    name: str
    url: str
    status_code: int
    status_msg: str | None = None
    status: str | None = None
    user_id: int
