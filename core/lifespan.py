from contextlib import asynccontextmanager
from typing import AsyncGenerator, Any
from multiprocessing import Manager
import asyncio
import logging

from core.scheduler import start_task_scheduler, stop_scheduler
from utils import cleanup_processes, get_optimal_process_count
from helper_class import TaskManager

logger = logging.getLogger("server")

@asynccontextmanager
async def lifespan(app: Any) -> AsyncGenerator[None, None]:
    # Shared state setup
    manager = Manager()
    shared_tasks = manager.dict()
    processes = {}
    queue = asyncio.Queue()

    app.state.task_manager = TaskManager(shared_tasks)
    app.state.shared_tasks = shared_tasks
    app.state.processes = processes
    app.state.queue = queue
    app.state.max_process = get_optimal_process_count() 

    scheduler_task = start_task_scheduler(app)
    app.state.scheduler_task = scheduler_task

    logger.info("Application started. Scheduler running.")

    try:
        yield
    finally:
        await stop_scheduler(app)
        await cleanup_processes(app)
        manager.shutdown()
        logger.info("Application shutdown complete.")