from typing import List
from psutil import Process
import psutil


def get_child_processes() -> List[Process]:
    current_process = psutil.Process()
    children = current_process.children(recursive=True)
    return children

def get_subprocess_count() -> int:
    return len(get_child_processes())


async def cleanup_processes(app):
     for task_id in list(app.state.processes.keys()):
        proc = app.state.processes[task_id]
        if proc.is_alive():
            continue
        proc.join()
        del app.state.processes[task_id]
        app.state.task_manager.remove_task(task_id)
        
        
