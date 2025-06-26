import asyncio, time, uvicorn, uuid
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Dict, Optional, Callable
from fastapi import FastAPI, HTTPException, WebSocket, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from multiprocessing import Manager, Process
# import multiprocessing
# from returns.pointfree import bind
# from returns.result import Result, Failure, Success
# from returns.maybe import Maybe
from utils import *

@dataclass(frozen=True)
class Task:
    id: str
    status: str

# --- Pure Functions ---

def create_task(task_id: str, status="queued") -> Task:
    return Task(
        id=task_id,
        status=status,
    )


class TaskManager:
    def __init__(self, shared_tasks: dict):
        self.tasks: Dict[str, Task] = shared_tasks

    def add_task(self, task: Task) -> None:
        self.tasks[task.id] = task

    def get_task(self, task_id: str) -> Optional[Task]:
        return self.tasks.get(task_id)

    def update_task(
        self, task_id: str, updater: Callable[[Task], Task]
    ) -> Optional[Task]:
        current = self.tasks[task_id]
        updated = updater(current)
        self.tasks[task_id] = updated
        return updated
    


@asynccontextmanager
async def lifespan(app: FastAPI):
    manager = Manager()
    shared_tasks = manager.dict()
    app.state.task_manager = TaskManager(shared_tasks)
    app.state.shared_tasks = shared_tasks
    app.state.processes = {}
    app.state.queue = asyncio.Queue()
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
        for p in app.state.processes.values():
            if p.is_alive():
                p.join()

app = FastAPI(title="Task Server", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def update_task(task: Task, **kwargs) -> Task:
    return Task(
        id=task.id,
        status=kwargs.get("status", task.status),
    )


# --- Task Logic ---


def complicated_task(task_id: str, shared_tasks : Dict[str, Task]) -> None:

    time.sleep(10)

    current_task = shared_tasks.get(task_id)
    updated_task = update_task(
        current_task,
        status="completed",
    )
    shared_tasks[task_id] = updated_task

# --- Utility Functions for Process Management ---


def cleanup_finished_processes(processes: dict) -> None:
    for task_id in list(processes.keys()):
        process = processes[task_id]
        if not process.is_alive():
            process.join()
            del processes[task_id]


async def task_scheduler(app: FastAPI) -> None:
    while True:
        cleanup_finished_processes(app.state.processes)

        if len(app.state.processes) < MAX_PROCESSES:
            try:
                task_id = app.state.queue.get_nowait()
            except asyncio.QueueEmpty:
                pass
            else:
                app.state.task_manager.update_task(
                    task_id, lambda t: update_task(t, status="running")
                )
                p = Process(target=complicated_task, args=(
                    task_id, app.state.shared_tasks))
                p.start()
                app.state.processes[task_id] = p

        await asyncio.sleep(1)



# --- API Endpoints ---

@app.get("/tasks/getid")
async def get_task_id() -> Dict[str, str]:
    return {"task_id": str(uuid.uuid4())}

@app.post("/tasks/start/{task_id}")
async def start_task(task_id: str, request_data: dict,request :Request) -> Dict[str, str]:
    task = create_task(task_id, status="queued")
    request.app.state.task_manager.add_task(task)
    
    await request.app.state.queue.put(task_id)
    return {"task_id": task_id, "status": task.status}


@app.post("/tasks/stop/{task_id}")
async def stop_task(task_id: str, request :Request) -> Dict[str, str]:
    updated = request.app.state.task_manager.update_task(
        task_id, lambda t: update_task(t, status="cancelled")
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"task_id": task_id, "status": "cancelled"}


@app.get('/tasks/list')
def list_tasks(request: Request):
    return request.app.state.task_manager.tasks

@app.websocket("/ws/{task_id}")
async def task_status_ws(websocket: WebSocket, task_id: str) -> None:
    task = app.state.task_manager.get_task(task_id)
    if not task:
        await websocket.close(code=1008, reason="Task not found")
        return

    await websocket.accept()
    while task.status not in ("completed", "cancelled"):
        await websocket.send_json(task.__dict__)
        await asyncio.sleep(2)

        task = app.state.task_manager.get_task(task_id)

    await websocket.send_json(task.__dict__)
    await websocket.close()


if __name__ == "__main__":
    uvicorn.run(app, host=HOST, port=PORT)


# run server : fastapi dev ./server.py