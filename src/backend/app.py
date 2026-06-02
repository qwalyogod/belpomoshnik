from contextlib import asynccontextmanager

from fastapi import FastAPI

from backend.api.admin import router as admin_router
from backend.api.auth import router as auth_router
from backend.api.public import router as public_router
from backend.api.situations import router as situations_router
from backend.api.user import router as user_router
from backend.database import engine
from backend.models import Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    from backend.scheduler import start_background_tasks, stop_background_tasks
    start_background_tasks()
    yield
    stop_background_tasks()


def create_app() -> FastAPI:
    app = FastAPI(
        title="Belpomoshnik API",
        description="API для управления жизненными сценариями приложения Белпомощник.",
        version="0.1.0",
        lifespan=lifespan,
    )
    app.include_router(public_router)
    app.include_router(admin_router)
    app.include_router(auth_router)
    app.include_router(user_router)
    app.include_router(situations_router)

    @app.get("/api/health", tags=["system"])
    def health():
        return {"status": "ok"}

    return app


app = create_app()


def init_database() -> None:
    Base.metadata.create_all(bind=engine)

