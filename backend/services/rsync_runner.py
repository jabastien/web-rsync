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


def _is_remote(path: str) -> bool:
    """True for user@host:/path or host:/path — false for local paths and rsync:// URLs."""
    if "://" in path or path.startswith("/") or path.startswith("./"):
        return False
    return ":" in path


def _parse_remote(path: str) -> tuple[str, str]:
    """Split 'user@host:/path' → ('user@host', '/path')."""
    host, _, remote_path = path.partition(":")
    return host, remote_path


def _build_rsync_cmd(task: Task, dry_run: bool = False) -> list[str]:
    options = shlex.split(task.rsync_options)
    if dry_run and "--dry-run" not in options and "-n" not in options:
        options = ["--dry-run"] + options
    ssh_key = settings.ssh_dir / "id_rsa"

    if _is_remote(task.source_path) and _is_remote(task.dest_path):
        # Remote→remote: SSH into source host and run rsync from there.
        # -A forwards the server's SSH agent so the source can authenticate
        # to the destination without the private key leaving the server.
        source_host, source_path = _parse_remote(task.source_path)
        inner_opts = options + ["-e", "ssh -o StrictHostKeyChecking=accept-new"]
        inner_cmd = ["rsync"] + inner_opts + [source_path, task.dest_path]
        inner_str = " ".join(shlex.quote(a) for a in inner_cmd)
        cmd = ["ssh", "-A", "-o", "StrictHostKeyChecking=accept-new"]
        if ssh_key.exists():
            cmd += ["-i", str(ssh_key)]
        cmd += [source_host, inner_str]
        return cmd

    if ssh_key.exists():
        options += ["-e", f"ssh -i {ssh_key} -o StrictHostKeyChecking=accept-new"]
    return ["rsync"] + options + [task.source_path, task.dest_path]


async def _start_run(task_id: int | None, trigger: str, cmd: list[str]) -> int:
    """Create JobRun record synchronously, fire rsync in background, return run_id."""
    db: Session = SessionLocal()
    try:
        settings.log_dir.mkdir(parents=True, exist_ok=True)
        job_run = JobRun(task_id=task_id, trigger=trigger, status="running", log_path="")
        db.add(job_run)
        db.flush()
        log_path = settings.log_dir / f"{job_run.id}.log"
        job_run.log_path = str(log_path)
        db.commit()
        run_id = job_run.id
    finally:
        db.close()

    logger.info("Starting run %d: %s", run_id, cmd)
    asyncio.create_task(_execute_semaphored(cmd, log_path, run_id))
    return run_id


async def run_task(task_id: int, trigger: str = "manual") -> int:
    db: Session = SessionLocal()
    try:
        task = db.get(Task, task_id)
        if not task:
            logger.error("Task %d not found", task_id)
            return -1
        cmd = _build_rsync_cmd(task)
    finally:
        db.close()
    return await _start_run(task_id, trigger, cmd)


async def run_dry(task_id: int) -> int:
    db: Session = SessionLocal()
    try:
        task = db.get(Task, task_id)
        if not task:
            return -1
        cmd = _build_rsync_cmd(task, dry_run=True)
    finally:
        db.close()
    return await _start_run(task_id, "dry_run", cmd)


async def run_preview(source_path: str, dest_path: str, rsync_options: str) -> int:
    """Ephemeral dry-run with arbitrary paths/options — no saved task required."""
    options = shlex.split(rsync_options)
    if "--dry-run" not in options and "-n" not in options:
        options = ["--dry-run"] + options
    if "-v" not in options and "--verbose" not in options:
        options = ["-v"] + options
    ssh_key = settings.ssh_dir / "id_rsa"
    if ssh_key.exists():
        options += ["-e", f"ssh -i {ssh_key} -o StrictHostKeyChecking=accept-new"]
    cmd = ["rsync"] + options + [source_path, dest_path]
    return await _start_run(None, "dry_run", cmd)


async def _execute_semaphored(cmd: list[str], log_path: Path, run_id: int) -> None:
    async with get_semaphore():
        await _execute(cmd, log_path, run_id)


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


def mark_stale_runs_failed(db: Session):
    stale = db.query(JobRun).filter(JobRun.status == "running").all()
    for run in stale:
        run.status = "failed"
        run.finished_at = datetime.now(timezone.utc)
        run.exit_code = -1
    if stale:
        db.commit()
        logger.warning("Marked %d stale job runs as failed", len(stale))
