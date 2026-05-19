from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.task import Task
from ..schemas.task import TaskCreate, TaskRead, TaskUpdate
from ..services import rsync_runner, scheduler as sched_svc


class PreviewRequest(BaseModel):
    source_path: str
    dest_path: str
    rsync_options: str = "-avz"

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


def _sync_scheduler(task: Task):
    if task.enabled and task.schedule:
        sched_svc.add_task_job(task.id, task.schedule, rsync_runner.run_task)
    else:
        sched_svc.remove_task_job(task.id)


@router.get("", response_model=list[TaskRead])
def list_tasks(db: Session = Depends(get_db)):
    return db.query(Task).all()


@router.post("", response_model=TaskRead, status_code=201)
def create_task(payload: TaskCreate, db: Session = Depends(get_db)):
    if db.query(Task).filter(Task.name == payload.name).first():
        raise HTTPException(409, "Task name already exists")
    task = Task(**payload.model_dump())
    db.add(task)
    db.commit()
    db.refresh(task)
    _sync_scheduler(task)
    return task


@router.post("/preview")
async def preview_task(payload: PreviewRequest):
    """Ephemeral dry-run with form values — no saved task required."""
    run_id = await rsync_runner.run_preview(
        payload.source_path, payload.dest_path, payload.rsync_options
    )
    return {"run_id": run_id}


@router.get("/{task_id}", response_model=TaskRead)
def get_task(task_id: int, db: Session = Depends(get_db)):
    task = db.get(Task, task_id)
    if not task:
        raise HTTPException(404, "Task not found")
    return task


@router.put("/{task_id}", response_model=TaskRead)
def update_task(task_id: int, payload: TaskUpdate, db: Session = Depends(get_db)):
    task = db.get(Task, task_id)
    if not task:
        raise HTTPException(404, "Task not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(task, k, v)
    db.commit()
    db.refresh(task)
    _sync_scheduler(task)
    return task


@router.patch("/{task_id}/enabled", response_model=TaskRead)
def toggle_task(task_id: int, enabled: bool, db: Session = Depends(get_db)):
    task = db.get(Task, task_id)
    if not task:
        raise HTTPException(404, "Task not found")
    task.enabled = enabled
    db.commit()
    db.refresh(task)
    _sync_scheduler(task)
    return task


@router.delete("/{task_id}", status_code=204)
def delete_task(task_id: int, db: Session = Depends(get_db)):
    task = db.get(Task, task_id)
    if not task:
        raise HTTPException(404, "Task not found")
    sched_svc.remove_task_job(task_id)
    db.delete(task)
    db.commit()


@router.post("/{task_id}/run")
async def run_task(task_id: int, db: Session = Depends(get_db)):
    task = db.get(Task, task_id)
    if not task:
        raise HTTPException(404, "Task not found")
    run_id = await rsync_runner.run_task(task_id, "manual")
    return {"run_id": run_id, "task_id": task_id}


@router.post("/{task_id}/dry-run")
async def dry_run_task(task_id: int, db: Session = Depends(get_db)):
    task = db.get(Task, task_id)
    if not task:
        raise HTTPException(404, "Task not found")
    run_id = await rsync_runner.run_dry(task_id)
    return {"run_id": run_id, "task_id": task_id}


@router.post("/{task_id}/clone", response_model=TaskRead, status_code=201)
def clone_task(task_id: int, db: Session = Depends(get_db)):
    task = db.get(Task, task_id)
    if not task:
        raise HTTPException(404, "Task not found")
    new_name = f"{task.name} (copy)"
    if db.query(Task).filter(Task.name == new_name).first():
        raise HTTPException(409, f"Task '{new_name}' already exists")
    clone = Task(
        name=new_name,
        source_path=task.source_path,
        dest_path=task.dest_path,
        rsync_options=task.rsync_options,
        schedule=None,  # Don't clone schedule to avoid duplicate jobs
        enabled=False,
    )
    db.add(clone)
    db.commit()
    db.refresh(clone)
    return clone
