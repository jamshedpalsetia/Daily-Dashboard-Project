from __future__ import annotations

import datetime as dt
import logging
from pathlib import Path
from zoneinfo import ZoneInfo

from jinja2 import Environment, FileSystemLoader, select_autoescape
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.email_sender import send_email
from app.models import DigestLog
from app.services import widgets
from app.services.settings_service import get_settings_row

log = logging.getLogger(__name__)

TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "templates"
_env = Environment(
    loader=FileSystemLoader(TEMPLATE_DIR),
    autoescape=select_autoescape(["html"]),
    trim_blocks=True,
    lstrip_blocks=True,
)


def _money(value) -> str:
    if value is None:
        return "—"
    if abs(value) >= 1_000_000_000:
        return f"${value / 1_000_000_000:,.1f}B"
    if abs(value) >= 1_000_000:
        return f"${value / 1_000_000:,.1f}M"
    return f"${value:,.2f}"


def _pct(value) -> str:
    return "—" if value is None else f"{value:+.2f}%"


def _signed(value) -> str:
    return "—" if value is None else f"{'+' if value >= 0 else '-'}${abs(value):,.2f}"


def _deg(value, unit: str = "") -> str:
    """Rounded temperature that tolerates a missing reading.

    Upstream can omit any individual field, and a template exception would mean
    no email at all, so nothing in the templates is allowed to assume a number.
    """
    if value is None:
        return "—"
    try:
        return f"{round(float(value))}{unit}"
    except (TypeError, ValueError):
        return "—"


_env.filters["money"] = _money
_env.filters["pct"] = _pct
_env.filters["signed"] = _signed
_env.filters["deg"] = _deg


def _safe(fn, fallback):
    try:
        return fn()
    except Exception as exc:  # noqa: BLE001 - a dead widget must not block the email
        log.warning("digest section failed: %s", exc)
        return fallback


def build_context(db: Session) -> dict:
    s = get_settings_row(db)
    tz = ZoneInfo(s.timezone) if s.timezone else dt.timezone.utc
    today = dt.datetime.now(tz).date()

    weather = _safe(lambda: widgets.weather_payload(db), {"weather": None})
    movers = _safe(lambda: widgets.movers_payload(db), {"movers": None})
    watchlist = _safe(lambda: widgets.watchlist_payload(db), {"holdings": [], "totals": {}})
    news = _safe(lambda: widgets.news_payload(db), {"news": None})
    deals = _safe(lambda: widgets.deals_payload(db), {"deals": []})
    todos = _safe(lambda: widgets.visible_todos(db), [])

    open_todos = [t for t in todos if not t.done]
    overdue = [t for t in open_todos if t.due_date and t.due_date < today]
    due_today = [t for t in open_todos if t.due_date == today]
    recently_done = [t for t in todos if t.done]

    return {
        "date_label": dt.datetime.now(tz).strftime("%A, %B %-d, %Y"),
        "location": s.location_label,
        "weather": weather.get("weather"),
        "movers": movers.get("movers"),
        "holdings": watchlist.get("holdings", []),
        "totals": watchlist.get("totals", {}),
        "news": news.get("news"),
        "deals": (deals.get("deals") or [])[:6],
        "open_todos": open_todos[:12],
        "overdue": overdue,
        "due_today": due_today,
        "recently_done": recently_done[:5],
        "dashboard_url": get_settings().dashboard_url,
        "today": today,
    }


def render(db: Session) -> tuple[str, str, str]:
    ctx = build_context(db)
    subject = f"Daily Dashboard — {ctx['date_label']}"

    weather = ctx.get("weather") or {}
    current = weather.get("current") or {}
    if current.get("temperature") is not None:
        unit = (weather.get("units") or {}).get("temperature", "")
        subject += f" · {round(current['temperature'])}{unit} {current.get('condition', {}).get('label', '')}".rstrip()

    html = _env.get_template("digest.html").render(**ctx)
    text = _env.get_template("digest.txt").render(**ctx)
    return subject, html, text


def send_digest(db: Session, trigger: str = "scheduled") -> dict:
    s = get_settings_row(db)
    tz = ZoneInfo(s.timezone) if s.timezone else dt.timezone.utc
    today = dt.datetime.now(tz).date()

    if trigger == "scheduled":
        already = db.scalar(
            select(DigestLog).where(
                DigestLog.sent_for_date == today,
                DigestLog.trigger == "scheduled",
                DigestLog.status == "sent",
            )
        )
        if already is not None:
            log.info("digest for %s already sent, skipping", today)
            return {"status": "skipped", "reason": "already sent today"}

    try:
        subject, html, text = render(db)
        send_email(s.email_to or "", subject, html, text)
    except Exception as exc:  # noqa: BLE001 - record the failure, don't crash the scheduler
        db.add(
            DigestLog(
                sent_for_date=today, trigger=trigger, status="failed", detail=str(exc)[:1000]
            )
        )
        db.commit()
        log.error("digest send failed: %s", exc)
        return {"status": "failed", "error": str(exc)}

    db.add(DigestLog(sent_for_date=today, trigger=trigger, status="sent"))
    db.commit()
    return {"status": "sent", "to": s.email_to, "subject": subject}
