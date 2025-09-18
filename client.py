import logging
import json
import asyncio
import aiohttp
import websockets
import argparse
from typing import Dict, Optional, Any

from const import BASE_URL, PORT, WS_URL
from helper_class import Command, Request_Type
from utils import timeit, setup_logging

logger = setup_logging("client")

def extract_task_id[T](data: Dict[str, T]) -> Optional[str]:
    return data.get("task_id")

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
        logger.exception(f"Request failed: {e}")
        return None

# --- Task Management ---
@timeit(logger=logger)
async def start_task(session: aiohttp.ClientSession, task_id: str) -> Dict[str,Any] | str:
    url: str = f"{BASE_URL}:{PORT}/tasks/start/{task_id}"
    result: Dict[str, Any] | None = await unified_request_handler(session, Request_Type.POST, url, json={})
    if result and "task_id" in result:
        logger.info(f"Task started: {task_id}")
        return task_id
    return None

@timeit(logger=logger)
async def stop_task(session: aiohttp.ClientSession, task_id: str) -> Dict[str,Any] | None:
    url: str = f"{BASE_URL}:{PORT}/tasks/stop/{task_id}"
    result: Dict[str, Any] | None = await unified_request_handler(session, Request_Type.POST, url)
    if result:
        logger.info(f"Task stopped: {task_id}")
    return result

@timeit(logger=logger)
async def list_tasks(session: aiohttp.ClientSession) -> Dict[str,Any] | None:
    url: str = f"{BASE_URL}:{PORT}/tasks/list"
    result: Dict[str, Any] | None = await unified_request_handler(session, Request_Type.GET, url)
    if result is not None:
        logger.info(f"Found {len(result)} tasks")
    return result


async def receive_ws_messages(ws: websockets.ClientConnection) -> None:
    async for message in ws:
        data = json.loads(message)
        logger.info(f"Status update: {json.dumps(data, indent=2)}")
        if data.get("status") in ("completed", "cancelled"):
            logger.info("Task completed or cancelled. Closing monitor.")
            break

async def listen_task_status(task_id: str) -> None:
    ws_url: str = f"{WS_URL}/{task_id}"
    try:
        async with websockets.connect(ws_url) as ws:
            logger.info(f"Connected to WebSocket: {ws_url}")
            await receive_ws_messages(ws)
    except Exception as e:
        logger.exception(f"Failed to connect WebSocket for task {task_id}: {e}")


def parse_arguments():
    parser = argparse.ArgumentParser(description='Client for task management API')

    # Restrict subcommands to Command enum values
    subparsers = parser.add_subparsers(
        dest='command',
        help='Available commands',
    )

    # Start command
    start = subparsers.add_parser(Command.START, help='Start a new task')

    # Stop command
    stop = subparsers.add_parser(Command.STOP, help='Stop a running task')
    stop.add_argument('--task_id', required=True, help='Task ID to stop')

    # List command
    subparsers.add_parser(Command.LIST, help='List all tasks')

    # Status command
    status = subparsers.add_parser(Command.STATUS, help='Monitor task status in real-time')
    status.add_argument('--task_id', required=True, help='Task ID to monitor')

    args = parser.parse_args()

    return args

# --- Main ---
async def main() -> None:
    args = parse_arguments()
    async with aiohttp.ClientSession() as session:
        task_id = None
        match args.command:
            case Command.START:
                id_response: Dict[str, Any] | None = await unified_request_handler(session, Request_Type.GET, f"{BASE_URL}:{PORT}/tasks/getid")
                task_id: str | None = extract_task_id(id_response)
                if not task_id:
                    logger.error("Failed to get task ID")
                    return

                await start_task(session, task_id)
                logger.info(f"Task {task_id} started. Use 'status {task_id}' to monitor.")
                
            
            case Command.STOP:
                task_id = args.task_id
                if not task_id:
                    logger.error("Missing task_id for stop command")
                    return
                await stop_task(session, task_id)
            
            
            case Command.LIST:
                result: Dict[str, Any] | None = await list_tasks(session)
                if result:
                    pretty_print(result)

            case Command.STATUS:
                task_id = args.task_id
                logger.info(f"Monitoring task: {task_id}")
                await listen_task_status(task_id)
                
            case _:
                logger.error(f"unknown command {args.command}")
                return 



if __name__ == "__main__":
    asyncio.run(main())