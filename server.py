import asyncio
from multiprocessing.managers import SyncManager
import time
import uvicorn
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Dict
from datetime import datetime
from multiprocessing import Manager, Process

from fastapi import FastAPI, HTTPException, WebSocket, status
from fastapi.middleware.cors import CORSMiddleware
from websockets import ConnectionClosedError, ConnectionClosedOK


from helper_class import Task, TaskStatus, TaskManager, get_optimal_process_count
from server_utils import cleanup_processes, get_subprocess_count
from utils import timeit
from const import HOST,PORT, QUEUE_CHECK, STATUS_FREQUENCY
from configs import setup_logging

logger = setup_logging("server")

@timeit(logger=logger)
def complicated_task(task_id: str, shared_tasks: dict) -> None:
    time.sleep(20)
    if task_id in shared_tasks:
        shared_tasks[task_id] = Task(status=TaskStatus.COMPLETED)
        
async def start_new_task(app: FastAPI) -> None:
    try:
        task_id = app.state.queue.get_nowait()
        app.state.task_manager.update_task(task_id, TaskStatus.RUNNING)
        p = Process(target=complicated_task, args=(task_id, app.state.shared_tasks))
        p.start()
        app.state.processes[task_id] = p
        logger.info(f"Prcess started with pid: {p.pid}")
    except asyncio.QueueEmpty:
        return
    
    
    
async def task_scheduler(app: FastAPI) -> None:
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

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[Any, None]:
    manager: SyncManager = Manager()
    shared_tasks = manager.dict()
    processes = {}
    queue = asyncio.Queue()

    app.state.task_manager = TaskManager(shared_tasks)
    app.state.shared_tasks = shared_tasks
    app.state.processes = processes
    app.state.queue = queue
    app.state.max_process = get_optimal_process_count()
    scheduler_task = asyncio.create_task(task_scheduler(app))
    app.state.scheduler_task = scheduler_task

    try:
        yield
    finally:
        scheduler_task.cancel()
        try:
            await scheduler_task
        except asyncio.CancelledError:
            pass

        for p in processes.values():
            if not p.is_alive():
                continue
            p.terminate()
            p.join(timeout=3)
            if not p.is_alive():
                continue
            p.kill()
            p.join()


@asynccontextmanager
async def managed_websocket(websocket: WebSocket) -> AsyncGenerator[WebSocket, None]:
    try:
        await websocket.accept()
        yield websocket
    except (ConnectionClosedOK, ConnectionClosedError):
        return
    except Exception as e:
        logger.warning(f"WebSocket error: {e}")
    finally:
        if getattr(websocket, "client_state", None) == "connected":
            await websocket.close(code=status.WS_1011_INTERNAL_ERROR, reason="Server Cleanup")


app = FastAPI(title="Task Server", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/tasks/getid")
async def get_task_id[T]() -> Dict[str, T]:
    task_id: str = datetime.now().strftime("%Y%m%d%H%M%S%f")
    return {"task_id": task_id}


@app.post("/tasks/start/{task_id}")
async def start_task(task_id: str) -> Dict[str,str]:
    app.state.task_manager.add_task(task_id, TaskStatus.QUEUED)
    await app.state.queue.put(task_id)
    return {"task_id": task_id, "status": TaskStatus.QUEUED}


@app.post("/tasks/stop/{task_id}")
async def stop_task(task_id: str) -> Dict[str, str]:
    success = app.state.task_manager.update_task(task_id, TaskStatus.CANCELLED)
    
    if not success:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return {"task_id": task_id, "status": TaskStatus.CANCELLED}


@app.get('/tasks/list')
def list_tasks() -> Dict[str,Dict[str,str]]:
    return {
        tid: {"status": task.status} 
        for tid, task in app.state.shared_tasks.items()
    }
    

@app.websocket("/ws/{task_id}")
async def task_status_ws(websocket: WebSocket, task_id: str) -> None:
    if task_id not in app.state.shared_tasks:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Task not found")
        return
    task = app.state.task_manager.get_task(task_id)
    if not task:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Task not found")
        return
    
    if task.status in (TaskStatus.CANCELLED, TaskStatus.COMPLETED):
        await websocket.close(code=status.WS_1000_NORMAL_CLOSURE)
        return
    
    async with managed_websocket(websocket=websocket):
        while True:
            await websocket.send_json({"task_id": task_id, "status": task.status})
            await asyncio.sleep(STATUS_FREQUENCY)


if __name__ == "__main__":
    uvicorn.run(app, host=HOST, port=PORT)
