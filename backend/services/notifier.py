# -----------------------------------------------------------------------------
# Author : Claude (claude-sonnet-4-6) — written with Alain's consent
# Date   : 2026-05-25
# -----------------------------------------------------------------------------
import asyncio
import json
import logging

import apprise
import httpx

from ..database import SessionLocal
from ..models.notification import NotificationChannel
from ..models.task import Task

logger = logging.getLogger(__name__)

_HTTP_TIMEOUT = httpx.Timeout(10.0)

VALID_PROVIDERS = {"ntfy", "gotify", "discord", "telegram", "apprise", "webhook"}

# ntfy emoji tag names (shown as icons in ntfy clients)
_NTFY_TAGS = {
    "success": "white_check_mark",
    "failed":  "rotating_light",
}


def _build_apprise_url(provider: str, cfg: dict, status: str = "") -> str:
    """Construct an Apprise URL from provider name + config dict."""
    if provider == "apprise":
        return cfg["apprise_url"]

    if provider == "ntfy":
        server: str = cfg["url"].rstrip("/")
        is_https = server.startswith("https://")
        server = server.removeprefix("https://").removeprefix("http://")
        topic = cfg["topic"]
        token = cfg.get("token", "")
        priority = cfg.get("priority", "default")
        auth = f"{token}@" if token else ""
        scheme = "ntfys" if is_https else "ntfy"
        tag = _NTFY_TAGS.get(status, "bell")
        return f"{scheme}://{auth}{server}/{topic}?priority={priority}&tags={tag}"

    if provider == "gotify":
        server: str = cfg["url"].rstrip("/")
        # Apprise uses gotifys:// for HTTPS — preserve the original scheme
        is_https = server.startswith("https://")
        server = server.removeprefix("https://").removeprefix("http://")
        token = cfg["token"]
        priority = cfg.get("priority", 5)
        scheme = "gotifys" if is_https else "gotify"
        return f"{scheme}://{server}/{token}?priority={priority}"

    if provider == "discord":
        # Webhook URL: https://discord.com/api/webhooks/<id>/<token>
        webhook_url: str = cfg["webhook_url"]
        parts = webhook_url.rstrip("/").split("/")
        webhook_id = parts[-2]
        webhook_token = parts[-1]
        return f"discord://{webhook_id}/{webhook_token}"

    if provider == "telegram":
        bot_token = cfg["bot_token"]
        chat_id = cfg["chat_id"]
        return f"tgram://{bot_token}/{chat_id}"

    raise ValueError(f"Unknown provider for Apprise URL build: {provider}")


def _format_duration(seconds: int) -> str:
    if seconds < 60:
        return f"{seconds}s"
    m, s = divmod(seconds, 60)
    return f"{m}m {s}s" if s else f"{m}m"


def _build_message(status: str, run_id: int, task_name: str,
                   exit_code: int | None, duration: int | None) -> tuple[str, str]:
    """Return (title, message) with emoji appropriate to the status."""
    if status == "success":
        icon = "✅"
        title = f"{icon} rsync success: {task_name}"
        lines = [f"Job #{run_id} completed successfully."]
    else:
        icon = "❌"
        title = f"{icon} rsync failed: {task_name}"
        lines = [f"Job #{run_id} failed."]
        if exit_code is not None:
            lines.append(f"🔴 Exit code: {exit_code}")

    if duration is not None:
        lines.append(f"⏱ Duration: {_format_duration(duration)}")

    return title, "  ".join(lines)


async def _send_via_apprise(apprise_url: str, title: str, message: str) -> None:
    ap = apprise.Apprise()
    ap.add(apprise_url)
    ok = await ap.async_notify(title=title, body=message)
    if not ok:
        raise RuntimeError("Apprise reported failure (check provider credentials/URL)")


async def _send_webhook(cfg: dict, title: str, message: str) -> None:
    url = cfg["url"]
    headers = dict(cfg.get("headers", {}))
    template = cfg.get("body_template", "")
    if template:
        body_str = template.replace("{{title}}", title).replace("{{message}}", message)
        body = json.loads(body_str)
    else:
        body = {"title": title, "message": message}
    async with httpx.AsyncClient(timeout=_HTTP_TIMEOUT) as client:
        r = await client.post(url, json=body, headers=headers)
        r.raise_for_status()


async def _dispatch_channel(
    channel: NotificationChannel, title: str, message: str, status: str
) -> None:
    """Send to one channel; log and swallow all exceptions so callers are never disrupted."""
    try:
        cfg = json.loads(channel.config)
        if channel.provider == "webhook":
            await _send_webhook(cfg, title, message)
        else:
            apprise_url = _build_apprise_url(channel.provider, cfg, status)
            await _send_via_apprise(apprise_url, title, message)
    except Exception:
        logger.exception(
            "Notification failed for channel %d (%s)", channel.id, channel.provider
        )


async def dispatch_job_result(task_id: int, run_id: int, status: str) -> None:
    """
    Called after a job run completes. Loads enabled channels from a fresh DB
    session and fires per-channel tasks. Fire-and-forget — called via create_task().
    """
    from ..models.job_run import JobRun  # avoid circular at module level

    db = SessionLocal()
    try:
        task = db.get(Task, task_id)
        if task is None or not task.notify_enabled:
            return

        job_run = db.get(JobRun, run_id)
        exit_code: int | None = job_run.exit_code if job_run else None
        duration: int | None = None
        if job_run and job_run.finished_at and job_run.started_at:
            delta = job_run.finished_at - job_run.started_at
            duration = max(0, int(delta.total_seconds()))

        channels = (
            db.query(NotificationChannel)
            .filter(NotificationChannel.enabled == True)  # noqa: E712
            .all()
        )
        relevant = [
            ch for ch in channels
            if (status == "success" and ch.notify_on_success)
            or (status == "failed" and ch.notify_on_failure)
        ]
        task_name = task.name
    finally:
        db.close()

    if not relevant:
        return

    title, message = _build_message(status, run_id, task_name, exit_code, duration)

    for ch in relevant:
        asyncio.create_task(_dispatch_channel(ch, title, message, status))


async def send_test(channel: NotificationChannel) -> None:
    """
    Awaited directly by the test endpoint — NOT fire-and-forget.
    Raises on failure so the HTTP response can carry the error.
    """
    title = "🔔 web-RSync Test"
    message = "✅ Test notification from web-RSync — your channel is working."
    cfg = json.loads(channel.config)
    if channel.provider == "webhook":
        await _send_webhook(cfg, title, message)
    else:
        apprise_url = _build_apprise_url(channel.provider, cfg, "success")
        await _send_via_apprise(apprise_url, title, message)
