from enum import IntEnum


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
