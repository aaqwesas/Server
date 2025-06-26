import os
from typing import Optional, Dict

PORT = 8000
HOST = "127.0.0.1"
BASE_URL = "http://127.0.0.1"
WS_URL = f"ws://127.0.0.1:{PORT}/ws"
MAX_PROCESSES = 2

def check_files_exist(file_paths: Dict[str, str]) -> Optional[str]:
    for key, path in file_paths.items():
        if not os.path.exists(path):
            return f"File not found for '{key}': {path}"
    return None


def make_session_dir(dir :str, task_id : str) -> str:
    session_dir = os.path.join(dir, str(task_id))
    os.makedirs(session_dir, exist_ok=True)
    return session_dir
