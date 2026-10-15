from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import get_db
from app.models import DigestLog
from app.services import digest as digest_service

router = APIRouter(prefix="/api/digest", tags=["digest"])


@router.get("/status")
def status(db: Session = Depends(get_db)) -> dict:
    recent = list(
        db.scalars(select(DigestLog).order_by(DigestLog.sent_at.desc()).limit(5))
    )
    return {
        "smtp_configured": get_settings().smtp_configured,
        "recent": [
            {
                "date": r.sent_for_date.isoformat(),
                "sent_at": r.sent_at.isoformat(),
                "trigger": r.trigger,
                "status": r.status,
                "detail": r.detail,
            }
            for r in recent
        ],
    }


@router.get("/preview", response_class=HTMLResponse)
def preview(db: Session = Depends(get_db)) -> HTMLResponse:
    """Render the email in the browser without sending it."""
    _, html, _ = digest_service.render(db)
    return HTMLResponse(html)


@router.post("/send-now")
def send_now(db: Session = Depends(get_db)) -> dict:
    result = digest_service.send_digest(db, trigger="manual")
    if result.get("status") == "failed":
        raise HTTPException(status_code=502, detail=result.get("error", "send failed"))
    return result
