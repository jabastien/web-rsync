# -----------------------------------------------------------------------------
# Author : Claude (claude-sonnet-4-6) — written with Alain's consent
# Date   : 2026-05-25
# -----------------------------------------------------------------------------
import json
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.notification import NotificationChannel
from ..schemas.notification import (
    NotificationChannelCreate,
    NotificationChannelRead,
    NotificationChannelUpdate,
)
from ..services import notifier

router = APIRouter(prefix="/api/notifications", tags=["notifications"])

VALID_PROVIDERS = {"ntfy", "gotify", "discord", "telegram", "apprise", "webhook"}


def _to_read(channel: NotificationChannel) -> NotificationChannelRead:
    """Convert ORM object to schema, deserializing the config JSON string."""
    data = {
        "id": channel.id,
        "name": channel.name,
        "provider": channel.provider,
        "config": json.loads(channel.config),
        "enabled": channel.enabled,
        "notify_on_success": channel.notify_on_success,
        "notify_on_failure": channel.notify_on_failure,
        "created_at": channel.created_at,
        "updated_at": channel.updated_at,
    }
    return NotificationChannelRead(**data)


@router.get("", response_model=list[NotificationChannelRead])
def list_channels(db: Session = Depends(get_db)):
    channels = db.query(NotificationChannel).order_by(NotificationChannel.id).all()
    return [_to_read(ch) for ch in channels]


@router.post("", response_model=NotificationChannelRead, status_code=201)
def create_channel(payload: NotificationChannelCreate, db: Session = Depends(get_db)):
    if payload.provider not in VALID_PROVIDERS:
        raise HTTPException(422, f"Unknown provider '{payload.provider}'")
    if db.query(NotificationChannel).filter(NotificationChannel.name == payload.name).first():
        raise HTTPException(409, "Channel name already exists")
    channel = NotificationChannel(
        name=payload.name,
        provider=payload.provider,
        config=json.dumps(payload.config),
        enabled=payload.enabled,
        notify_on_success=payload.notify_on_success,
        notify_on_failure=payload.notify_on_failure,
    )
    db.add(channel)
    db.commit()
    db.refresh(channel)
    return _to_read(channel)


@router.get("/{channel_id}", response_model=NotificationChannelRead)
def get_channel(channel_id: int, db: Session = Depends(get_db)):
    channel = db.get(NotificationChannel, channel_id)
    if not channel:
        raise HTTPException(404, "Channel not found")
    return _to_read(channel)


@router.put("/{channel_id}", response_model=NotificationChannelRead)
def update_channel(
    channel_id: int, payload: NotificationChannelUpdate, db: Session = Depends(get_db)
):
    channel = db.get(NotificationChannel, channel_id)
    if not channel:
        raise HTTPException(404, "Channel not found")
    if payload.provider is not None and payload.provider not in VALID_PROVIDERS:
        raise HTTPException(422, f"Unknown provider '{payload.provider}'")
    updates = payload.model_dump(exclude_none=True)
    if "config" in updates:
        updates["config"] = json.dumps(updates["config"])
    for k, v in updates.items():
        setattr(channel, k, v)
    db.commit()
    db.refresh(channel)
    return _to_read(channel)


@router.delete("/{channel_id}", status_code=204)
def delete_channel(channel_id: int, db: Session = Depends(get_db)):
    channel = db.get(NotificationChannel, channel_id)
    if not channel:
        raise HTTPException(404, "Channel not found")
    db.delete(channel)
    db.commit()


@router.post("/{channel_id}/test")
async def test_channel(channel_id: int, db: Session = Depends(get_db)):
    channel = db.get(NotificationChannel, channel_id)
    if not channel:
        raise HTTPException(404, "Channel not found")
    try:
        await notifier.send_test(channel)
        return {"detail": "Test notification sent successfully"}
    except Exception as e:
        raise HTTPException(502, f"Notification failed: {e}")
