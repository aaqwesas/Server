from enum import StrEnum, auto

class TaskStatus(StrEnum):
    QUEUED = auto()
    RUNNING = auto()
    COMPLETED = auto()
    CANCELLED = auto()
    FAILED = auto()