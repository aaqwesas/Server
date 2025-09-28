from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


from core.lifespan import lifespan
from tasks import tasks_router
from ws import ws_router


def create_app() -> FastAPI:
    app = FastAPI(title="Task Server", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(tasks_router)
    app.include_router(ws_router)

    return app