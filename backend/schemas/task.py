from datetime import datetime
from pydantic import BaseModel, field_validator
from apscheduler.triggers.cron import CronTrigger


class TaskBase(BaseModel):
    name: str
    source_path: str
    dest_path: str
    rsync_options: str = "-avz"
    exclude_patterns: str = ""
    include_patterns: str = ""
    schedule: str | None = None
    enabled: bool = True


class TaskCreate(TaskBase):
    @field_validator("schedule")
    @classmethod
    def validate_schedule(cls, v: str | None) -> str | None:
        if v:
            try:
                CronTrigger.from_crontab(v)
            except Exception as e:
                raise ValueError(f"Invalid cron expression: {e}")
        return v


class TaskUpdate(BaseModel):
    name: str | None = None
    source_path: str | None = None
    dest_path: str | None = None
    rsync_options: str | None = None
    exclude_patterns: str | None = None
    include_patterns: str | None = None
    schedule: str | None = None
    enabled: bool | None = None

    @field_validator("schedule")
    @classmethod
    def validate_schedule(cls, v: str | None) -> str | None:
        if v:
            try:
                CronTrigger.from_crontab(v)
            except Exception as e:
                raise ValueError(f"Invalid cron expression: {e}")
        return v


class TaskRead(TaskBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
