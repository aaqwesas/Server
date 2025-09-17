import asyncio
import time
import uvicorn
from contextlib import asynccontextmanager
from helper_class import Task, TaskStatus, TaskManager, get_optimal_process_count
from typing import Any, AsyncGenerator, Dict
from fastapi import FastAPI, HTTPException, WebSocket, Request
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from multiprocessing import Manager, Process



from const import HOST,PORT



@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[Any, None]:
    manager = Manager()
    shared_tasks = manager.dict()
    processes = {}
    queue = asyncio.Queue()

    app.state.task_manager = TaskManager(shared_tasks)
    app.state.shared_tasks = shared_tasks
    app.state.processes = processes
    app.state.queue = queue

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
            if p.is_alive():
                p.terminate()
                p.join(timeout=3)
                if p.is_alive():
                    p.kill()
                    p.join()

app = FastAPI(title="Task Server", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



# --- Task Logic ---
def complicated_task(task_id: str, shared_tasks: dict) -> None:
    time.sleep(5)
    if task_id in shared_tasks:
        shared_tasks[task_id] = Task(status=TaskStatus.COMPLETED)



async def task_scheduler(app: FastAPI) -> None:
    max_process = get_optimal_process_count()
    print(f"{max_process = }")
    while True:
        # Clean up finished processes
        for task_id in list(app.state.processes.keys()):
            proc = app.state.processes[task_id]
            if not proc.is_alive():
                proc.join()
                del app.state.processes[task_id]
                app.state.task_manager.remove_task(task_id)
        # Start new tasks if room
        if len(app.state.processes) < max_process:
            try:
                task_id = app.state.queue.get_nowait()
                app.state.task_manager.update_task(task_id, TaskStatus.RUNNING)
                p = Process(target=complicated_task, args=(task_id, app.state.shared_tasks))
                p.start()
                app.state.processes[task_id] = p
            except asyncio.QueueEmpty:
                pass
        await asyncio.sleep(1)


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
async def stop_task(task_id: str, request :Request) -> Dict[str, str]:
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
        await websocket.close(code=1008, reason="Task not found")
        return

    await websocket.accept()
    try:
        while True:
            task = app.state.task_manager.get_task(task_id)
            if not task:
                await websocket.close(code=1008, reason="Task deleted")
                return

            await websocket.send_json({"task_id": task_id, "status": task.status})

            if task.status in (TaskStatus.CANCELLED, TaskStatus.COMPLETED):
                break

            await asyncio.sleep(2)
    finally:
        await websocket.close()


if __name__ == "__main__":
    uvicorn.run(app, host=HOST, port=PORT)
