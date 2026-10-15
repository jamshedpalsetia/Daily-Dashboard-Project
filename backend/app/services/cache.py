from __future__ import annotations

import datetime as dt
import logging
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models import CacheEntry

log = logging.getLogger(__name__)


@dataclass
class CachedResult:
    data: Any
    stale: bool
    fetched_at: dt.datetime
    error: str | None = None

    def as_response(self, key: str = "data") -> dict:
        return {
            key: self.data,
            "stale": self.stale,
            "fetched_at": self.fetched_at.isoformat(),
            "error": self.error,
        }


def _now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def cached(
    db: Session,
    key: str,
    ttl_seconds: int,
    fetch: Callable[[], Any],
) -> CachedResult:
    """Return cached data if fresh, otherwise refetch.

    If the refetch fails but a stale entry exists, the stale entry is served
    with `stale=True` rather than surfacing an error — a flaky upstream should
    degrade a widget, not blank it.
    """
    now = _now()
    entry = db.get(CacheEntry, key)

    if entry is not None and entry.expires_at > now:
        return CachedResult(data=entry.payload["v"], stale=False, fetched_at=entry.fetched_at)

    try:
        data = fetch()
    except Exception as exc:  # noqa: BLE001 - any upstream failure degrades to cache
        log.warning("cache refresh failed for %s: %s", key, exc)
        if entry is not None:
            return CachedResult(
                data=entry.payload["v"],
                stale=True,
                fetched_at=entry.fetched_at,
                error=str(exc),
            )
        raise

    stmt = (
        insert(CacheEntry)
        .values(
            key=key,
            payload={"v": data},
            fetched_at=now,
            expires_at=now + dt.timedelta(seconds=ttl_seconds),
        )
        .on_conflict_do_update(
            index_elements=["key"],
            set_={
                "payload": {"v": data},
                "fetched_at": now,
                "expires_at": now + dt.timedelta(seconds=ttl_seconds),
            },
        )
    )
    db.execute(stmt)
    db.commit()

    return CachedResult(data=data, stale=False, fetched_at=now)


def invalidate(db: Session, key: str) -> None:
    entry = db.get(CacheEntry, key)
    if entry is not None:
        db.delete(entry)
        db.commit()
