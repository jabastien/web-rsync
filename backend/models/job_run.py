from datetime import datetime
from sqlalchemy import String, Integer, ForeignKey, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..database import Base


class JobRun(Base):
    __tablename__ = "job_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    task_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("tasks.id"), nullable=True)
    trigger: Mapped[str] = mapped_column(String, default="manual")  # manual|scheduled|dry_run|preview
    started_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    exit_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String, default="running")  # running|success|failed|cancelled
    log_path: Mapped[str] = mapped_column(String, nullable=False)

    task: Mapped["Task | None"] = relationship("Task", back_populates="job_runs")


from .task import Task  # noqa: E402, F401
