from contextlib import asynccontextmanager
from typing import AsyncGenerator, Any
from multiprocessing import Manager
import asyncio
import logging

from core.middleware import RateLimiter, rate_limit_reset_scheduler, stop_rate_limit_scheduler
from core.scheduler import start_task_scheduler, stop_scheduler
from utils import cleanup_processes, get_optimal_process_count
from helper_class import TaskManager

logger = logging.getLogger("server")

@asynccontextmanager
async def lifespan(app: Any) -> AsyncGenerator[None, None]:
    max_requests = 5
    reset_interval_seconds = 20
    manager = Manager()
    
    
    shared_tasks = manager.dict()

    app.state.limiter = RateLimiter(max_requests=max_requests, reset_interval_seconds=reset_interval_seconds)
    app.state.shared_tasks = shared_tasks
    app.state.processes = {}
    app.state.queue = asyncio.Queue()
    app.state.scheduler_event = asyncio.Event()
    app.state.task_manager = TaskManager(shared_tasks)
    app.state.max_process = get_optimal_process_count()
    app.state.scheduler_task = start_task_scheduler(app)
    app.state.scheduler_rate = rate_limit_reset_scheduler(app.state.limiter)

    try:
        yield
    finally:
        await stop_scheduler(app)
        await stop_rate_limit_scheduler(app)
        await cleanup_processes(app)
        manager.shutdown()