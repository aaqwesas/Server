from typing import Dict, Optional
from helper_class.task import Task
from helper_class.task_status import TaskStatus
import dataclasses



class TaskManager:
    def __init__(self, shared_tasks: Dict[str, Task]) -> None:
        self.tasks: Dict[str, Task] = shared_tasks

    def remove_task(self, task_id: str) -> bool:
        return self.tasks.pop(task_id, None)

    def add_task(self, task_id: str, status: str = TaskStatus.QUEUED) -> None:
        self.tasks[task_id] = Task(status=status)

    def get_task(self, task_id: str) -> Optional[Task]:
        return self.tasks.get(task_id)

    def update_task(self, task_id: str, status: str) -> bool:
        if task_id not in self.tasks:
            return False
        self.tasks[task_id] = dataclasses.replace(self.tasks[task_id],status=status)
        return True