from contextlib import asynccontextmanager

from dotenv import load_dotenv

# Load secrets (e.g. GROQ_API_KEY) from a gitignored .env before reading env.
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.api.admin import router as admin_router
from backend.api.articles import router as articles_router
from backend.api.assistant import router as assistant_router
from backend.api.auth import router as auth_router
from backend.api.public import router as public_router
from backend.api.situations import router as situations_router
from backend.api.trackers import router as trackers_router
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
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://127.0.0.1:8560",
            "http://localhost:8560",
            "http://127.0.0.1:8550",
            "http://localhost:8550",
            # LAN-адрес для live-reload: iPhone-приложение через Capacitor
            # тянет Vite с ПК. Меняй, если ПК переехал в другую сеть.
            "http://192.168.100.95:8560",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(public_router)
    app.include_router(admin_router)
    app.include_router(auth_router)
    app.include_router(user_router)
    app.include_router(situations_router)
    app.include_router(trackers_router)
    app.include_router(articles_router)
    app.include_router(assistant_router)

    from backend.api.articles import UPLOAD_DIR
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR), check_dir=False), name="uploads")

    # v0.3: PDF сканы личных документов. Отдельный mount, чтобы не путать
    # пользовательский контент (документы) и редакторский (статьи).
    from backend.api.user import DOCUMENT_SCAN_DIR
    DOCUMENT_SCAN_DIR.mkdir(parents=True, exist_ok=True)
    app.mount(
        "/uploads/documents",
        StaticFiles(directory=str(DOCUMENT_SCAN_DIR), check_dir=False),
        name="document-scans",
    )

    @app.get("/api/health", tags=["system"])
    def health():
        return {"status": "ok"}

    return app


app = create_app()


def init_database() -> None:
    Base.metadata.create_all(bind=engine)
