from enum import IntEnum


class UserRole(IntEnum):
    USER = 0
    ADMIN = 1


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
