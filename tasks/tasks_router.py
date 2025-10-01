import logging
from typing import Any, Dict
import datetime


from fastapi import APIRouter, HTTPException, Request

from helper_class import TaskStatus


logger = logging.getLogger("server")

tasks_router = APIRouter(
    prefix="/tasks",
    tags=["Task utility"]
)

@tasks_router.get("/getid")
def get_task_id[T]() -> Dict[str, T]:
    task_id: str = datetime.datetime.now().strftime("%Y%m%d%H%M%S%f")
    return {"task_id": task_id}


@tasks_router.post("/start/{task_id}")
async def start_task(request: Request,task_id: str) -> Dict[str,str]:
    request.app.state.task_manager.add_task(task_id, TaskStatus.QUEUED)
    await request.app.state.queue.put(task_id)
    return {"task_id": task_id, "status": TaskStatus.QUEUED}


@tasks_router.post("/stop/{task_id}")
def stop_task(request: Request,task_id: str ) -> Dict[str, str]:
    success = request.app.state.task_manager.update_task(task_id, TaskStatus.CANCELLED)
    
    if not success:
        raise HTTPException(status_code=404, detail="Task not found")
    
    logger.info(f"Task {task_id} stopped.")
    
    return {"task_id": task_id, "status": TaskStatus.CANCELLED}


@tasks_router.get('/list')
def list_tasks(request: Request) -> Dict[str,Dict[str,str]]:
    return {
        tid: {"status": task.status} 
        for tid, task in request.app.state.shared_tasks.items()
    }
@tasks_router.get("/health", tags=["Health Checks"])
def health_check() -> Dict[str, Any]:
    return {
        "status": "healthy",
        "service": "task-manager",
        "timestamp": datetime.datetime.now(datetime.timezone.utc)
    }
    

