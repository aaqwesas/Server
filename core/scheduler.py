import asyncio
import logging
from multiprocessing import Process
from typing import Any

from fastapi import FastAPI
from configs import QUEUE_CHECK
from worker import complicated_task
from helper_class import TaskStatus

from utils import cleanup_processes

logger = logging.getLogger("server")

async def start_new_task(app: FastAPI) -> bool:
    try:
        task_id = app.state.queue.get_nowait()
    except asyncio.QueueEmpty:
        return False
    app.state.task_manager.update_task(task_id, TaskStatus.RUNNING)
    p = Process(target=complicated_task, args=(task_id, app.state.shared_tasks))
    p.start()
    app.state.processes[task_id] = p
    logger.info("Process started with pid: %s",p.pid)
    app.state.queue.task_done()
    return True
 

async def task_scheduler(app: Any) -> None:
    max_process = app.state.max_process
    print(f"{max_process = }")
    
    while True:
        await cleanup_processes(app=app)
        current_processes = len(app.state.processes)
        
        if current_processes < max_process:
            started = await start_new_task(app)
            if started:
                continue
        
        if current_processes >= max_process:
            logger.debug("Max processes reached. Waiting for free slot...")
            await app.state.scheduler_event.wait()
            app.state.scheduler_event.clear()
        else:
            await asyncio.sleep(QUEUE_CHECK)
        


async def stop_scheduler(app: Any) -> None:
    if not hasattr(app.state, "scheduler_task"):
        return
    app.state.scheduler_task.cancel()
    try:
        await app.state.scheduler_task
    except asyncio.CancelledError:
        logger.info("Scheduler task cancelled.")
        
        
def start_task_scheduler(app: Any) -> asyncio.Task:
    return asyncio.create_task(task_scheduler(app))