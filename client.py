from src.const import BASE_URL, PORT, WS_URL
import time
import logging
import json
import asyncio
import aiohttp
import websockets
import argparse
from functools import wraps
from typing import Dict, Optional, Any

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# --- Decorators ---
def with_logging(func):
    @wraps(func)
    async def wrapper(*args, **kwargs) -> Any:
        start_time = time.time()
        result = await func(*args, **kwargs)
        end_time = time.time()
        logger.info(f"Function {func.__name__} took {end_time - start_time:.2f}s")
        return result
    return wrapper

# --- Utilities ---
def extract_task_id[T](data: Dict[str, T]) -> Optional[str]:
    return data.get("task_id")

def pretty_print(data) -> None:
    logger.info(json.dumps(data, indent=2, ensure_ascii=False))

# --- HTTP Client ---
@with_logging
async def unified_request_handler(
    session: aiohttp.ClientSession,
    method: str,
    url: str,
    params: dict = None,
    data: dict = None,
    json: dict = None,
    headers: dict = None,
    timeout: int = 10,
) -> Optional[Dict[str,Any]]:
    try:
        async with session.request(
            method=method.upper(),
            url=url,
            params=params,
            data=data,
            json=json,
            headers=headers,
            timeout=timeout,
        ) as response:
            if response.status >= 400:
                text: str = await response.text()
                logger.error(f"HTTP {response.status}: {text}")
                return None
            return await response.json()
    except Exception as e:
        logger.exception(f"Request failed: {e}")
        return None

# --- Task Management ---
@with_logging
async def start_task(session: aiohttp.ClientSession, task_id: str) -> Dict[str,Any] | str:
    url: str = f"{BASE_URL}:{PORT}/tasks/start/{task_id}"
    result: Dict[str, Any] | None = await unified_request_handler(session, "post", url, json={})
    if result and "task_id" in result:
        logger.info(f"Task started: {task_id}")
        return task_id
    return None

@with_logging
async def stop_task(session: aiohttp.ClientSession, task_id: str) -> Dict[str,Any] | None:
    url: str = f"{BASE_URL}:{PORT}/tasks/stop/{task_id}"
    result: Dict[str, Any] | None = await unified_request_handler(session, "post", url)
    if result:
        logger.info(f"Task stopped: {task_id}")
    return result

@with_logging
async def list_tasks(session: aiohttp.ClientSession) -> Dict[str,Any] | None:
    url: str = f"{BASE_URL}:{PORT}/tasks/list"
    result: Dict[str, Any] | None = await unified_request_handler(session, "get", url)
    if result is not None:
        logger.info(f"Found {len(result)} tasks")
    return result


async def receive_ws_messages(ws: websockets.ClientConnection) -> None:
    try:
        async for message in ws:
            data = json.loads(message)
            logger.info(f"📡 Status update: {json.dumps(data, indent=2)}")
            if data.get("status") in ("completed", "cancelled"):
                logger.info("✅ Task completed or cancelled. Closing monitor.")
                break
    except websockets.ConnectionClosed as e:
        logger.info(f"WebSocket closed: {e}")

async def listen_task_status(task_id: str) -> None:
    ws_url: str = f"{WS_URL}/{task_id}"
    try:
        async with websockets.connect(ws_url) as ws:
            logger.info(f"🌐 Connected to WebSocket: {ws_url}")
            await receive_ws_messages(ws)
    except Exception as e:
        logger.exception(f"Failed to connect WebSocket for task {task_id}: {e}")


def parse_arguments():
    parser = argparse.ArgumentParser(
        description='Client for task management API'
    )
    subparsers = parser.add_subparsers(dest='command', help='Available commands', required=True)

    # start command
    start: argparse.ArgumentParser = subparsers.add_parser('start', help='Start a new task')
    start.add_argument('--task-id', type=str, help='Specify task ID (optional)')

    # stop command
    stop: argparse.ArgumentParser = subparsers.add_parser('stop', help='Stop a running task')
    stop.add_argument('task_id', nargs='?', help='Task ID to stop')

    # list command
    subparsers.add_parser('list', help='List all tasks')

    # status command (monitor via WebSocket)
    status: argparse.ArgumentParser = subparsers.add_parser('status', help='Monitor task status in real-time')
    status.add_argument('task_id', help='Task ID to monitor')

    return parser.parse_args()

# --- Main ---
async def main() -> None:
    args = parse_arguments()

    async with aiohttp.ClientSession() as session:
        task_id = None

        if args.command == "start":
            id_response: Dict[str, Any] | None = await unified_request_handler(session, "get", f"{BASE_URL}:{PORT}/tasks/getid")
            task_id: str | None = extract_task_id(id_response)
            if not task_id:
                logger.error("Failed to get task ID")
                return

            await start_task(session, task_id)
            logger.info(f"Task {task_id} started. Use 'status {task_id}' to monitor.")

        elif args.command == "stop":
            task_id = args.task_id
            if not task_id:
                logger.error("Missing task_id for stop command")
                return
            await stop_task(session, task_id)

        elif args.command == "list":
            result: Dict[str, Any] | None = await list_tasks(session)
            if result:
                pretty_print(result)

        elif args.command == "status":
            task_id = args.task_id
            logger.info(f"Monitoring task: {task_id}")
            await listen_task_status(task_id)

if __name__ == "__main__":
    asyncio.run(main())