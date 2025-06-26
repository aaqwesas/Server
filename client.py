import sys ,time, logging, json, asyncio, aiohttp, websockets, argparse
from functools import wraps
from utils import *
# from returns.pointfree import bind
from typing import Dict, Optional

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# --- Decorators ---


def with_logging(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        result = await func(*args, **kwargs)
        end_time = time.time()
        logger.info(
            f"Function {func.__name__} took {end_time - start_time} seconds")
        logger.info(f"Result from {func.__name__}: {result}")
        return result
    return wrapper

# ---pure functions---


def extract_task_id(data: Dict[str, Optional[str | None]]) -> Optional[str | None]:
    return data.get("task_id")


def pretty_print(data):
    logger.info(json.dumps(data, indent=2, ensure_ascii=False))

# --- HTTP Task Start Functions ---


async def unified_request_handler(
    session: aiohttp.ClientSession,
    method: str,
    url: str,
    params: dict = None,
    data: dict = None,
    json: dict = None,
    headers: dict = None,
    timeout: int = 10,
    **kwargs
) -> Optional[dict]:
    try:
        async with session.request(
            method=method.upper(),
            url=url,
            params=params,
            data=data,
            json=json,
            headers=headers,
            timeout=timeout,
            **kwargs
        ) as response:
            response.raise_for_status()
            return await response.json()
    except Exception as e:
        logger.exception(f"Request failed: {e}")
        return None


async def start_task(session: aiohttp.ClientSession, task_id: str, data: dict) -> str | None:
    try:
        await unified_request_handler(session, "post", f"{BASE_URL}:{PORT}/tasks/start/{task_id}", json={})
        return task_id
    except Exception as e:
        logger.exception(f"session creation failed: {e}")
        return None

# -----------------------
# WebSocket Message Handling Functions
# -----------------------


def safe_parse_json(message: str) -> dict | None:
    try:
        return json.loads(message)
    except json.JSONDecodeError:
        return None


async def process_ws_message(message: str) -> None:
    data = safe_parse_json(message)
    if data:
        pretty_print(data)


async def receive_ws_messages(ws: websockets.ClientConnection) -> None:
    while True:
        try:
            message = await ws.recv()
            await process_ws_message(message)
        except (websockets.ConnectionClosedOK, websockets.ConnectionClosedError) as e:
            logger.info(f"WebSocket connection closed")
            break

# -----------------------
# WebSocket Connection Management
# -----------------------


async def connect_to_websocket(task_id: str) -> websockets.ClientConnection:
    ws_endpoint = f"{WS_URL}/{task_id}"
    return await websockets.connect(ws_endpoint)


async def wait_for_task_completion(*tasks) -> list:
    done, pending = await asyncio.wait(
        [*tasks],
        return_when=asyncio.FIRST_COMPLETED
    )

    for task in pending:
        task.cancel()

    return [task.result() for task in done]


async def manage_websocket_connection(ws: websockets.ClientConnection) -> list | None:
    task_recv = asyncio.create_task(receive_ws_messages(ws))
    return await wait_for_task_completion(task_recv)


async def listen_task_status(task_id: str) -> list | None:
    try:
        ws = await connect_to_websocket(task_id)
        async with ws:
            return await manage_websocket_connection(ws)
    except Exception as e:
        logger.exception(
            f"WebSocket connection failed for task {task_id}: {e}")
        return None

# -----------------------
# Main Workflow Functions
# -----------------------


def parse_arguments():
    parser = argparse.ArgumentParser(
        description='Long-running process management API client')
    subparsers = parser.add_subparsers(
        dest='command', help='Available commands')

    # start command
    start_parser = subparsers.add_parser('start', help='Start a new task')

    # stop command
    stop_parser = subparsers.add_parser('stop', help='Stop a task')
    
    # list command
    list_parser = subparsers.add_parser('list', help='List all tasks')


    return parser.parse_args()


async def main() -> None:
    # Create the session within an async context
    async with aiohttp.ClientSession() as session:
        json_task_id = await unified_request_handler(session, "get", f"{BASE_URL}:{PORT}/tasks/getid")
        task_id = extract_task_id(json_task_id)

        args = parse_arguments()
        if args.command == 'start':
            task_id = await start_task(session, task_id, {})
            if task_id:
                logger.info(f"Started task with ID: {task_id}")
                result = await listen_task_status(task_id)
        elif args.command == 'stop':
            result = await unified_request_handler(session, "get", f"{BASE_URL}:{PORT}/tasks/stop/{task_id}")
        elif args.command == 'list':
            result = await unified_request_handler(session, "get", f"{BASE_URL}:{PORT}/tasks/list")

        pretty_print(result)

if __name__ == "__main__":

    # Start Cmd for function_id=0
    sys.argv = ["client.py", "start"]

    asyncio.run(main())

    # # Stop Cmd
    # sys.argv = ["client.py", "stop"]
    # main()

    # List Cmd
    # sys.argv = ["client.py", "list"]
    # main()