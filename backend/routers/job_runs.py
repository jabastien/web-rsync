import asyncio
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query
from sse_starlette.sse import EventSourceResponse
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.job_run import JobRun
from ..schemas.job_run import JobRunRead

router = APIRouter(prefix="/api/job-runs", tags=["job-runs"])


@router.get("", response_model=list[JobRunRead])
def list_job_runs(
    task_id: int | None = Query(None),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    q = db.query(JobRun).order_by(JobRun.started_at.desc())
    if task_id is not None:
        q = q.filter(JobRun.task_id == task_id)
    return q.limit(limit).all()


@router.delete("", status_code=200)
def purge_job_runs(db: Session = Depends(get_db)):
    """Delete all completed runs and their log files. Running jobs are not touched."""
    runs = db.query(JobRun).filter(JobRun.status != "running").all()
    for run in runs:
        if run.log_path:
            log = Path(run.log_path)
            try:
                log.unlink(missing_ok=True)
            except Exception:
                pass
        db.delete(run)
    db.commit()
    return {"deleted": len(runs)}


@router.get("/{run_id}", response_model=JobRunRead)
def get_job_run(run_id: int, db: Session = Depends(get_db)):
    run = db.get(JobRun, run_id)
    if not run:
        raise HTTPException(404, "Job run not found")
    return run


@router.get("/{run_id}/log")
def get_log(run_id: int, db: Session = Depends(get_db)):
    run = db.get(JobRun, run_id)
    if not run:
        raise HTTPException(404, "Job run not found")
    log = Path(run.log_path)
    if not log.exists():
        return {"log": ""}
    return {"log": log.read_text(errors="replace")}


@router.get("/{run_id}/stream")
async def stream_log(run_id: int, db: Session = Depends(get_db)):
    run = db.get(JobRun, run_id)
    if not run:
        raise HTTPException(404, "Job run not found")
    log_path = Path(run.log_path)

    async def event_generator():
        # Wait for log file to appear (up to 5s)
        for _ in range(50):
            if log_path.exists():
                break
            await asyncio.sleep(0.1)

        position = 0
        while True:
            if log_path.exists():
                text = log_path.read_text(errors="replace")
                if len(text) > position:
                    new_text = text[position:]
                    position = len(text)
                    for line in new_text.splitlines():
                        yield {"data": line}

            # Expire the cached object to force a fresh SELECT on next attribute access
            db.expire(run)
            if run.status != "running":
                yield {"event": "done", "data": run.status}
                return

            await asyncio.sleep(0.5)

    return EventSourceResponse(event_generator())
