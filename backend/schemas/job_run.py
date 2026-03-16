from datetime import datetime
from pydantic import BaseModel


class JobRunRead(BaseModel):
    id: int
    task_id: int
    trigger: str
    started_at: datetime
    finished_at: datetime | None
    exit_code: int | None
    status: str
    log_path: str

    model_config = {"from_attributes": True}
