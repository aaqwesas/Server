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
    manager = Manager()
    
    shared_tasks = manager.dict()

    app.state.shared_tasks = shared_tasks
    app.state.processes = {}
    app.state.queue = asyncio.Queue()
    app.state.scheduler_event = asyncio.Event()
    app.state.task_manager = TaskManager(shared_tasks)
    app.state.max_process = get_optimal_process_count()
    app.state.scheduler_task = start_task_scheduler(app)

    try:
        yield
    finally:
        logger.info("Shutting down...")
        await stop_scheduler(app)
        logger.debug("Scheduler stopped.")
        await cleanup_processes(app)
        logger.debug("Cleanup of finished processes completed.")
        manager.shutdown()
        logger.info("Application shutdown complete.")