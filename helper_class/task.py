from dataclasses import dataclass
from .task_status import TaskStatus


@dataclass(frozen=True)
class Task:
    status: TaskStatus
    
    def __post_init__(self) -> None:
        if isinstance(self.status, TaskStatus):
            return
        raise ValueError(
            f"Invalid Status: {self.status}. Must be one of {[status for status in TaskStatus]}"
        )
