import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator
import logging

from fastapi import APIRouter, WebSocket
from fastapi import status
from websockets import ConnectionClosedError, ConnectionClosedOK

from configs import STATUS_FREQUENCY
from helper_class import TaskStatus

logger = logging.getLogger("server")


ws_router = APIRouter(
    prefix="/ws",
    tags=["Websocket endpoint"]
)

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

@ws_router.websocket("/{task_id}")
async def task_status_ws(websocket: WebSocket, task_id: str) -> None:
    app = websocket.app

    if task_id not in app.state.shared_tasks:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Task not found")
        return

    async with managed_websocket(websocket):
        while True:
            task = app.state.task_manager.get_task(task_id)
            if not task:
                await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Task not found")
                return

            await websocket.send_json({"task_id": task_id, "status": task.status})

            if task.status in (TaskStatus.FAILED):
                await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
                return
            
            if task.status in (TaskStatus.CANCELLED, TaskStatus.COMPLETED):
                await websocket.close(code=status.WS_1000_NORMAL_CLOSURE)
                return

            await asyncio.sleep(STATUS_FREQUENCY)
