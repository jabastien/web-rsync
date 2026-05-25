import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from sqlalchemy import text

from .config import settings
from .database import Base, SessionLocal, engine
from .routers import hosts, job_runs, notifications, system, tasks
from .services import rsync_runner, scheduler as sched_svc
from .services.ssh_manager import ensure_ssh_key, ensure_ssh_agent, stop_ssh_agent
from .models import task as _task_model  # noqa: F401 — ensure models are registered
from .models import host as _host_model  # noqa: F401
from .models import job_run as _job_run_model  # noqa: F401
from .models import notification as _notification_model  # noqa: F401

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    settings.log_dir.mkdir(parents=True, exist_ok=True)

    Base.metadata.create_all(bind=engine)

    # Inline migration: add pattern columns to existing databases
    with engine.connect() as conn:
        for col in ("exclude_patterns", "include_patterns"):
            try:
                conn.execute(text(f"ALTER TABLE tasks ADD COLUMN {col} TEXT NOT NULL DEFAULT ''"))
                conn.commit()
            except Exception:
                pass  # column already exists

        try:
            conn.execute(text("ALTER TABLE tasks ADD COLUMN notify_enabled BOOLEAN NOT NULL DEFAULT 1"))
            conn.commit()
        except Exception:
            pass  # column already exists

    db = SessionLocal()
    try:
        rsync_runner.mark_stale_runs_failed(db)

        # Reload scheduled tasks
        from .models.task import Task
        tasks_list = db.query(Task).filter(Task.enabled == True, Task.schedule != None).all()
        for task in tasks_list:
            sched_svc.add_task_job(task.id, task.schedule, rsync_runner.run_task)
    finally:
        db.close()

    ensure_ssh_key()
    ensure_ssh_agent()
    sched_svc.scheduler.start()
    logger.info("web-RSync %s started", os.environ.get("APP_VERSION", "dev"))

    yield

    # Shutdown
    sched_svc.scheduler.shutdown(wait=False)
    stop_ssh_agent()
    logger.info("web-RSync stopped")


app = FastAPI(title="web-RSync", version=os.environ.get("APP_VERSION", "dev"), lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(tasks.router)
app.include_router(hosts.router)
app.include_router(job_runs.router)
app.include_router(system.router)
app.include_router(notifications.router)

# Serve Vue frontend in production (built files at /app/static)
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    # Mount built assets (JS/CSS) at /assets — Vite always outputs here
    assets_dir = static_dir / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

    # SPA catch-all: return index.html for every non-API path so Vue Router
    # can handle client-side navigation and direct URL access
    @app.get("/{full_path:path}")
    async def spa_fallback(full_path: str):
        return FileResponse(str(static_dir / "index.html"))
