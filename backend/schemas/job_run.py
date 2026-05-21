from datetime import datetime, timezone
from pydantic import BaseModel, field_serializer


class JobRunRead(BaseModel):
    id: int
    task_id: int | None
    task_name: str | None = None
    trigger: str
    started_at: datetime
    finished_at: datetime | None
    exit_code: int | None
    status: str

    model_config = {"from_attributes": True}

    @field_serializer("started_at")
    def serialize_started(self, dt: datetime) -> str:
        return dt.replace(tzinfo=timezone.utc).isoformat()

    @field_serializer("finished_at")
    def serialize_finished(self, dt: datetime | None) -> str | None:
        if dt is None:
            return None
        return dt.replace(tzinfo=timezone.utc).isoformat()
