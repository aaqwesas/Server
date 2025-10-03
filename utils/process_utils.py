import asyncio
from typing import List, Tuple
from fastapi import FastAPI
from psutil import Process
import psutil

from helper_class import TaskStatus
from configs import setup_logging

logger = setup_logging("server")

def get_child_processes() -> List[Process]:
    current_process = psutil.Process()
    children = current_process.children(recursive=True)
    return children

def get_subprocess_count() -> int:
    return len(get_child_processes())


async def cleanup_processes(app: FastAPI) -> None:
    loop = asyncio.get_running_loop()
    processes_to_clean: List[Tuple[str,Process]] = list(app.state.processes.items())
    for task_id, proc in processes_to_clean:
        task = app.state.task_manager.get_task(task_id)
        if task.status in (TaskStatus.CANCELLED, TaskStatus.COMPLETED, TaskStatus.FAILED):

            if proc.exitcode is None:
                proc.terminate()
                logger.debug("Terminated process %s", task_id)

            try:
                await loop.run_in_executor(None, proc.join, 3)
            except Exception as e:
                logger.warning("Join failed for %s: %s", task_id, e)

            if proc.is_alive():
                logger.warning("Process %s did not terminate, forcing kill", task_id)
                proc.kill()
                await loop.run_in_executor(None, proc.join)

            app.state.task_manager.remove_task(task_id)
            app.state.processes.pop(task_id, None)
            logger.info("Cleaned up resources for task %s", task_id)



