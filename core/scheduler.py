import asyncio
import logging
from multiprocessing import Process
from typing import Any

from fastapi import FastAPI
from configs import QUEUE_CHECK
from worker import complicated_task
from helper_class import TaskStatus

from utils import cleanup_processes, get_subprocess_count

logger = logging.getLogger("server")

async def start_new_task(app: FastAPI) -> None:
    try:
        task_id = app.state.queue.get_nowait()
        app.state.task_manager.update_task(task_id, TaskStatus.RUNNING)
        p = Process(target=complicated_task, args=(task_id, app.state.shared_tasks))
        p.start()
        app.state.processes[task_id] = p
        logger.info(f"Process started with pid: {p.pid}")
    except asyncio.QueueEmpty:
        return

async def task_scheduler(app: Any) -> None:
    max_process = app.state.max_process
    print(f"{max_process = }")
    
    while True:
        await cleanup_processes(app=app)
        processes = get_subprocess_count()
        if processes >= max_process:
            await asyncio.sleep(QUEUE_CHECK)
            continue
        await start_new_task(app=app)
        await asyncio.sleep(QUEUE_CHECK)

def start_task_scheduler(app: Any) -> asyncio.Task:
    return asyncio.create_task(task_scheduler(app))

async def stop_scheduler(app: Any) -> None:
        app.state.scheduler_task.cancel()
        try:
            await app.state.scheduler_task
        except asyncio.CancelledError:
            pass