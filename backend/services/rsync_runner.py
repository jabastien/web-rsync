import asyncio
import logging
import shlex
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy.orm import Session

from ..config import settings
from ..database import SessionLocal
from ..models.job_run import JobRun
from ..models.task import Task

logger = logging.getLogger(__name__)

_semaphore: asyncio.Semaphore | None = None


def get_semaphore() -> asyncio.Semaphore:
    global _semaphore
    if _semaphore is None:
        _semaphore = asyncio.Semaphore(settings.max_concurrent_jobs)
    return _semaphore


def _build_rsync_cmd(task: Task) -> list[str]:
    options = shlex.split(task.rsync_options)
    ssh_key = settings.ssh_dir / "id_rsa"
    if ssh_key.exists():
        options += ["-e", f"ssh -i {ssh_key} -o StrictHostKeyChecking=accept-new"]
    return ["rsync"] + options + [task.source_path, task.dest_path]


async def run_task(task_id: int, trigger: str = "manual") -> int:
    db: Session = SessionLocal()
    try:
        task = db.get(Task, task_id)
        if not task:
            logger.error("Task %d not found", task_id)
            return -1

        settings.log_dir.mkdir(parents=True, exist_ok=True)

        job_run = JobRun(
            task_id=task_id,
            trigger=trigger,
            status="running",
            log_path="",  # filled in below
        )
        db.add(job_run)
        db.flush()

        log_path = settings.log_dir / f"{job_run.id}.log"
        job_run.log_path = str(log_path)
        db.commit()
        run_id = job_run.id
        cmd = _build_rsync_cmd(task)
    finally:
        db.close()

    logger.info("Starting rsync run %d: %s", run_id, cmd)

    async with get_semaphore():
        exit_code = await _execute(cmd, log_path, run_id)

    return run_id


async def run_dry(task_id: int) -> int:
    db: Session = SessionLocal()
    try:
        task = db.get(Task, task_id)
        if not task:
            return -1

        settings.log_dir.mkdir(parents=True, exist_ok=True)
        job_run = JobRun(
            task_id=task_id,
            trigger="dry_run",
            status="running",
            log_path="",
        )
        db.add(job_run)
        db.flush()

        log_path = settings.log_dir / f"{job_run.id}.log"
        job_run.log_path = str(log_path)
        db.commit()
        run_id = job_run.id

        # Build command with --dry-run injected
        options = shlex.split(task.rsync_options)
        if "--dry-run" not in options and "-n" not in options:
            options = ["--dry-run"] + options
        ssh_key = settings.ssh_dir / "id_rsa"
        if ssh_key.exists():
            options += ["-e", f"ssh -i {ssh_key} -o StrictHostKeyChecking=accept-new"]
        cmd = ["rsync"] + options + [task.source_path, task.dest_path]
    finally:
        db.close()

    logger.info("Starting dry-run %d: %s", run_id, cmd)

    async with get_semaphore():
        exit_code = await _execute(cmd, log_path, run_id)

    return run_id


async def _execute(cmd: list[str], log_path: Path, run_id: int) -> int:
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )

        with open(log_path, "w") as log_file:
            assert proc.stdout is not None
            async for line in proc.stdout:
                log_file.write(line.decode(errors="replace"))
                log_file.flush()

        exit_code = await proc.wait()
    except Exception as e:
        logger.exception("Error executing rsync run %d", run_id)
        exit_code = -1
        with open(log_path, "a") as log_file:
            log_file.write(f"\n[ERROR] {e}\n")

    db: Session = SessionLocal()
    try:
        job_run = db.get(JobRun, run_id)
        if job_run:
            job_run.finished_at = datetime.now(timezone.utc)
            job_run.exit_code = exit_code
            job_run.status = "success" if exit_code == 0 else "failed"
            db.commit()
    finally:
        db.close()

    return exit_code


async def run_preview(source_path: str, dest_path: str, rsync_options: str) -> int:
    """Ephemeral dry-run with arbitrary paths/options — no saved task required.

    Creates the JobRun record synchronously and returns run_id immediately.
    Rsync executes as a background task so the caller can stream SSE right away.
    """
    db: Session = SessionLocal()
    try:
        settings.log_dir.mkdir(parents=True, exist_ok=True)
        job_run = JobRun(task_id=None, trigger="dry_run", status="running", log_path="")
        db.add(job_run)
        db.flush()
        log_path = settings.log_dir / f"{job_run.id}.log"
        job_run.log_path = str(log_path)
        db.commit()
        run_id = job_run.id
    finally:
        db.close()

    options = shlex.split(rsync_options)
    if "--dry-run" not in options and "-n" not in options:
        options = ["--dry-run"] + options
    if "-v" not in options and "--verbose" not in options:
        options = ["-v"] + options
    ssh_key = settings.ssh_dir / "id_rsa"
    if ssh_key.exists():
        options += ["-e", f"ssh -i {ssh_key} -o StrictHostKeyChecking=accept-new"]
    cmd = ["rsync"] + options + [source_path, dest_path]

    logger.info("Starting preview dry-run %d: %s", run_id, cmd)
    asyncio.create_task(_execute_semaphored(cmd, log_path, run_id))
    return run_id


async def _execute_semaphored(cmd: list[str], log_path: Path, run_id: int) -> None:
    async with get_semaphore():
        await _execute(cmd, log_path, run_id)


def mark_stale_runs_failed(db: Session):
    stale = db.query(JobRun).filter(JobRun.status == "running").all()
    for run in stale:
        run.status = "failed"
        run.finished_at = datetime.now(timezone.utc)
        run.exit_code = -1
    if stale:
        db.commit()
        logger.warning("Marked %d stale job runs as failed", len(stale))
