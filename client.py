import json
import asyncio
import aiohttp
import websockets
import argparse
from typing import Dict, Optional, Any

from configs import BASE_URL, PORT, WS_URL
from helper_class import Command, Request_Type, TaskStatus
from utils import timeit
from configs import setup_logging

logger = setup_logging("client")


def extract_task_id[T](data: Dict[str, T]) -> Optional[str]:
    try:
        return data.get("task_id")
    except Exception as e:
        logger.error(f"unable to get task id: {e}")

def pretty_print(data) -> None:
    logger.info(json.dumps(data, indent=2, ensure_ascii=False))

# --- HTTP Client ---
@timeit(logger=logger)
async def unified_request_handler(
    session: aiohttp.ClientSession,
    method: str,
    url: str,
    params: dict = None,
    data: dict = None,
    json: dict = None,
    headers: dict = None,
    timeout: int = 30,
) -> Optional[Dict[str,Any]]:
    try:
        async with session.request(
            method=method,
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
        logger.error(f"Request failed: {e}")

# --- Task Management ---
@timeit(logger=logger)
async def start_task(session: aiohttp.ClientSession, task_id: str) -> None:
    url: str = f"{BASE_URL}:{PORT}/tasks/start/{task_id}"
    result: Dict[str, Any] | None = await unified_request_handler(session, Request_Type.POST, url, json={})
    if result.get("task_id"):
        logger.info(f"Task started: {task_id}")

@timeit(logger=logger)
async def stop_task(session: aiohttp.ClientSession, task_id: str) -> Dict[str,Any] | None:
    url: str = f"{BASE_URL}:{PORT}/tasks/stop/{task_id}"
    result: Dict[str, Any] | None = await unified_request_handler(session, Request_Type.POST, url)
    if result:
        logger.info(f"Task stopped: {task_id}")

@timeit(logger=logger)
async def list_tasks(session: aiohttp.ClientSession) -> Dict[str,Any] | None:
    url: str = f"{BASE_URL}:{PORT}/tasks/list"
    result: Dict[str, Any] | None = await unified_request_handler(session, Request_Type.GET, url)
    if result is not None:
        logger.info(f"Found {len(result)} tasks")
        pretty_print(result)
        
@timeit(logger=logger) 
async def handle_start(session : aiohttp.ClientSession) -> None:
    url: str = f"{BASE_URL}:{PORT}/tasks/getid"
    id_response: Dict[str, Any] | None = await unified_request_handler(
        session, Request_Type.GET, url
        )
    task_id: str = extract_task_id(id_response)
    if not task_id:
        return
    await start_task(session, task_id)

async def handle_health_check(session: aiohttp.ClientSession) -> None:
    url = f"{BASE_URL}:{PORT}/tasks/health"
    result  = await unified_request_handler(
        session, Request_Type.GET, url
    )
    if result:
        pretty_print(result)
    

async def receive_ws_messages(ws: websockets.ClientConnection) -> None:
    async for message in ws:
        data = json.loads(message)
        logger.info(f"Status update: {json.dumps(data, indent=2)}")
        task_status = data.get("status")
        if task_status in (TaskStatus.COMPLETED, TaskStatus.CANCELLED, TaskStatus.FAILED):
            logger.info(f"Task in status {task_status}, Closing monitor.")
            break

async def listen_task_status(task_id: str) -> None:
    ws_url: str = f"{WS_URL}/{task_id}"
    try:
        async with websockets.connect(ws_url) as ws:
            logger.info(f"Connected to WebSocket: {ws_url}")
            await receive_ws_messages(ws)
    except Exception as e:
        logger.error(f"Failed to connect WebSocket for {task_id}: {e}")


def parse_arguments():
    parser = argparse.ArgumentParser(description='Client for task management API')

    # Restrict subcommands to Command enum values
    subparsers = parser.add_subparsers(
        dest='command',
        help='Available commands',
    )

    # Start command
    start = subparsers.add_parser(Command.START, help='Start a new task')  # noqa: F841

    # Stop command
    stop = subparsers.add_parser(Command.STOP, help='Stop a running task')
    stop.add_argument('--task_id', required=True, help='Task ID to stop')

    # List command
    subparsers.add_parser(Command.LIST, help='List all tasks')

    # Status command
    status = subparsers.add_parser(Command.STATUS, help='Monitor task status in real-time')
    status.add_argument('--task_id', required=True, help='Task ID to monitor')
    
    # server health check
    health = subparsers.add_parser(Command.HEALTH, help="simple health check for the server")

    args = parser.parse_args()

    return args


# --- Main ---
async def main() -> None:
    args = parse_arguments()
    command = args.command
    async with aiohttp.ClientSession() as session:
        match command:
            case Command.START:
                await handle_start(session=session)
                
            case Command.STOP:
                await stop_task(session=session, task_id=args.task_id)

            case Command.LIST:
                await list_tasks(session=session)

            case Command.STATUS:
                logger.info(f"Monitoring task: {args.task_id}")
                await listen_task_status(args.task_id)
                
            case Command.HEALTH:
                await handle_health_check(session=session)
                
                
            case _:
                logger.error(f"unknown command {command}")
                return 
        



if __name__ == "__main__":
    asyncio.run(main())