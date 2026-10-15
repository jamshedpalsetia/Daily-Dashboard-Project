from __future__ import annotations

import logging
from zoneinfo import ZoneInfo

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.db import SessionLocal
from app.services.digest import send_digest
from app.services.settings_service import get_settings_row

log = logging.getLogger(__name__)

DIGEST_JOB_ID = "daily-digest"

scheduler = BackgroundScheduler()


def _run_digest() -> None:
    db = SessionLocal()
    try:
        result = send_digest(db, trigger="scheduled")
        log.info("scheduled digest: %s", result)
    finally:
        db.close()


def apply_digest_schedule() -> None:
    """(Re)install the cron job from whatever is currently in the settings row.

    Called on startup and again whenever the digest time, timezone, or enabled
    flag changes, so schedule edits take effect without a restart.
    """
    db = SessionLocal()
    try:
        s = get_settings_row(db)
        enabled, hour, minute, tz_name = (
            s.digest_enabled,
            s.digest_hour,
            s.digest_minute,
            s.timezone,
        )
    finally:
        db.close()

    if scheduler.get_job(DIGEST_JOB_ID):
        scheduler.remove_job(DIGEST_JOB_ID)

    if not enabled:
        log.info("daily digest disabled")
        return

    try:
        tz = ZoneInfo(tz_name)
    except Exception:  # noqa: BLE001
        log.warning("unknown timezone %s, falling back to UTC", tz_name)
        tz = ZoneInfo("UTC")

    scheduler.add_job(
        _run_digest,
        trigger=CronTrigger(hour=hour, minute=minute, timezone=tz),
        id=DIGEST_JOB_ID,
        replace_existing=True,
        misfire_grace_time=3600,
        coalesce=True,
    )
    log.info("daily digest scheduled for %02d:%02d %s", hour, minute, tz_name)


def start() -> None:
    if not scheduler.running:
        scheduler.start()
    apply_digest_schedule()


def shutdown() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)
