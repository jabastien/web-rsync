# -----------------------------------------------------------------------------
# Author : Claude (claude-sonnet-4-6) — written with Alain's consent
# Date   : 2026-05-25
# -----------------------------------------------------------------------------
from datetime import datetime
from sqlalchemy import String, Integer, Boolean, DateTime, Text, func
from sqlalchemy.orm import Mapped, mapped_column
from ..database import Base


class NotificationChannel(Base):
    __tablename__ = "notification_channels"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    # provider: ntfy | gotify | discord | telegram | apprise | webhook
    provider: Mapped[str] = mapped_column(String, nullable=False)
    # config: JSON string — schema varies per provider (see notifier.py)
    config: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, server_default="1")
    notify_on_success: Mapped[bool] = mapped_column(Boolean, default=False, server_default="0")
    notify_on_failure: Mapped[bool] = mapped_column(Boolean, default=True, server_default="1")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
