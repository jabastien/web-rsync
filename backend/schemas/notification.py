# -----------------------------------------------------------------------------
# Author : Claude (claude-sonnet-4-6) — written with Alain's consent
# Date   : 2026-05-25
# -----------------------------------------------------------------------------
from datetime import datetime
from typing import Any
from pydantic import BaseModel


class NotificationChannelBase(BaseModel):
    name: str
    provider: str  # ntfy | gotify | discord | telegram | apprise | webhook
    config: dict[str, Any]
    enabled: bool = True
    notify_on_success: bool = False
    notify_on_failure: bool = True


class NotificationChannelCreate(NotificationChannelBase):
    pass


class NotificationChannelUpdate(BaseModel):
    name: str | None = None
    provider: str | None = None
    config: dict[str, Any] | None = None
    enabled: bool | None = None
    notify_on_success: bool | None = None
    notify_on_failure: bool | None = None


class NotificationChannelRead(NotificationChannelBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
