import logging
import os
from zoneinfo import ZoneInfo
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)

_tz = ZoneInfo(os.environ.get("TZ", "UTC"))
scheduler = AsyncIOScheduler(timezone=_tz)


def add_task_job(task_id: int, cron: str, run_fn):
    job_id = f"task_{task_id}"
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)
    scheduler.add_job(
        run_fn,
        trigger=CronTrigger.from_crontab(cron),
        id=job_id,
        args=[task_id, "scheduled"],
        replace_existing=True,
    )
    logger.info("Scheduled job %s with cron '%s'", job_id, cron)


def remove_task_job(task_id: int):
    job_id = f"task_{task_id}"
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)
        logger.info("Removed scheduled job %s", job_id)


def list_jobs():
    return [
        {
            "id": job.id,
            "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
            "trigger": str(job.trigger),
        }
        for job in scheduler.get_jobs()
    ]
