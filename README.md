# Server Application Template

A robust, production-ready server application built with Python. Designed for scalability, observability, and maintainability.

---

## Features

- RESTful API endpoints
- WebSocket support for real-time updates
- Configurable logging (file + console)
- Async I/O with `asyncio`
- Graceful startup/shutdown via lifespan
- Process/task management
- Health check endpoint
- Centralized error handling
- Queue for maximum process management
- Unit & integration tests (to be implemented)

---

## Tech Stack

| Layer | Technology |
|------|------------|
| Framework | FastAPI / Starlette *(or Flask / Custom)* |
| Runtime | Python 3.11+ |
| Logging | `python-logging` with JSON formatter |
| Processes | `multiprocessing` or `asyncio.subprocess` |
| Packaging | `pyproject.toml` |
| Testing | `unittest`, |

---

## 📦 Installation

```bash
git clone https://github.com/aaqwesas/Server.git
cd Server

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

Or install in dev mode:
```bash
pip install -e .
```

---

## ▶️ Run the Server

### Development Mode
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```
or 
```bash
python server.py
```
```bash
python -m fastapi dev server.py
```

---

## 🌐 API Endpoints

| Method | Path | Description |
|-------|------|-------------|
| `GET` | `/health` | Health check |
| `GET` | `/tasks/getid`  | generate unique id for client |
| `GET` | `/tasks/list` | List all tasks |
| `GET` | `/tasks/status/{task_id}` | Monitor task status |
| `POST` | `/tasks/start` | Start a new task |
| `POST` | `/tasks/stop/{task_id}` | Stop a running task |
| `WS`  | `/ws/{task_id}` | Real-time WebSocket updates |

👉 See [API Docs](http://localhost:8000/docs) (Swagger UI)

---

## 📝 Logging

Logs are written to:
- Console (stdout)
- File: `logs/server.log` (rotated)
- File: `logs/client.log`  (rotated)

Format:
```json
{"time": "2025-01-01 11:11:11", "level": "INFO", "logger": "client", "message": "your_message"}
```
---

## 🧪 Testing (to be implemented)

Run tests:
```bash
pytest tests/ -v
```

Coverage:
```bash
pytest --cov=app tests/
```

Includes:
- API endpoint tests
- Task lifecycle validation
- WebSocket mock testing

---

## 🔄 Lifecycle Management

Uses FastAPI’s `lifespan` for:
- Setup: Initialize `TaskManager`, `shared_tasks`, scheduler
- Cleanup: Terminate processes gracefully on shutdown
- Resource management: Queue, state, logging

See `server.py`.

---

## Error Handling

- Client disconnects on WebSocket → no error log
- Invalid task ID → `404` or `1008` close code
- Internal errors → logged at warning level
- Graceful process termination with timeout + kill

---

## Extending the Template (to be included)

- Database (SQLAlchemy, Tortoise ORM)
- JWT authentication
- Rate limiting
- Email alerts


---

## Acknowledgments

Built using:
- [FastAPI](https://fastapi.tiangolo.com/)
- [Uvicorn](https://www.uvicorn.org/)
- [Python Logging](https://docs.python.org/3/library/logging.html)
- [Websockets](https://websockets.readthedocs.io/en/stable/index.html#)
