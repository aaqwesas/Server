import uvicorn

from core import create_app
from configs import setup_logging

logger = setup_logging("server")

app = create_app()


if __name__ == "__main__":
    from configs import HOST, PORT
    uvicorn.run("server:app", host=HOST, port=PORT)