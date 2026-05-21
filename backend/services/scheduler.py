import logging
import os
from zoneinfo import ZoneInfo
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)

_tz = ZoneInfo(os.environ.get("TZ", "UTC"))
scheduler = AsyncIOScheduler(timezone=_tz)

# APScheduler uses 0=Monday; POSIX cron uses 0=Sunday.
# from_crontab() does not remap numeric day-of-week values, so we do it here.
_DOW_NAMES = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']

def _fix_dow(cron: str) -> str:
    parts = cron.strip().split()
    if len(parts) == 5:
        dow = parts[4]
        if dow != '*':
            try:
                parts[4] = _DOW_NAMES[int(dow) % 7 - 1] if int(dow) != 0 else 'sun'
            except ValueError:
                pass  # named or range expression — leave as-is
    return ' '.join(parts)


def add_task_job(task_id: int, cron: str, run_fn):
    job_id = f"task_{task_id}"
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)
    scheduler.add_job(
        run_fn,
        trigger=CronTrigger.from_crontab(_fix_dow(cron), timezone=_tz),
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
