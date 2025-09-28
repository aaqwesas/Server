import time
from helper_class import Task, TaskStatus
import logging

from utils import timeit


logger = logging.getLogger("server")

@timeit(logger=logger)
def complicated_task(task_id: str, shared_tasks: dict) -> None:
    time.sleep(15)
    if task_id in shared_tasks:
        shared_tasks[task_id] = Task(status=TaskStatus.COMPLETED)