from typing import Dict, Optional
from helper_class.task import Task
from helper_class.task_state import TaskStatus



class TaskManager:
    def __init__(self, shared_tasks: Dict[str, Task]) -> None:
        self.tasks: Dict[str, Task] = shared_tasks
        
    def remove_task(self,task_id):
        self.tasks.pop(task_id, "Does not exist")

    def add_task(self, task_id: str, status:str = TaskStatus.QUEUED) -> None:
        self.tasks[task_id] = Task(status=status)

    def get_task(self, task_id: str) -> Optional[Task]:
        return self.tasks.get(task_id)

    def update_task(self, task_id: str, status: str) -> bool:
        if task_id not in self.tasks:
            return False
        self.tasks[task_id] = Task(status=status)
        return True

    def list_tasks(self) -> Dict[str, Task]:
        return self.tasks.copy()