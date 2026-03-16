from fastapi import APIRouter
from ..services.scheduler import list_jobs

router = APIRouter(prefix="/api/system", tags=["system"])


@router.get("/health")
def health():
    return {"status": "ok"}


@router.get("/scheduler-jobs")
def scheduler_jobs():
    return list_jobs()
