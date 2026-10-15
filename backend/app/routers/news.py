from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.services import widgets

router = APIRouter(prefix="/api/news", tags=["news"])


@router.get("")
def read_news(db: Session = Depends(get_db)) -> dict:
    try:
        return widgets.news_payload(db)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=503, detail=f"news unavailable: {exc}") from exc
