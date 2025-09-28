from core.app import create_app
import uvicorn

from configs import setup_logging

logger = setup_logging("server")

app = create_app()


if __name__ == "__main__":
    from configs import HOST, PORT
    uvicorn.run(app, host=HOST, port=PORT)