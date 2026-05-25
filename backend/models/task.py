from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..database import Base


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    source_path: Mapped[str] = mapped_column(String, nullable=False)
    dest_path: Mapped[str] = mapped_column(String, nullable=False)
    rsync_options: Mapped[str] = mapped_column(String, default="-avz")
    exclude_patterns: Mapped[str] = mapped_column(String, default="", server_default="")
    include_patterns: Mapped[str] = mapped_column(String, default="", server_default="")
    schedule: Mapped[str | None] = mapped_column(String, nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    notify_enabled: Mapped[bool] = mapped_column(Boolean, default=True, server_default="1")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    job_runs: Mapped[list["JobRun"]] = relationship(
        "JobRun", back_populates="task", cascade="all, delete-orphan"
    )


from .job_run import JobRun  # noqa: E402, F401
