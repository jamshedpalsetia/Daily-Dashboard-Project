from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.services import widgets

router = APIRouter(prefix="/api/travel", tags=["travel"])


@router.get("/deals")
def read_deals(db: Session = Depends(get_db)) -> dict:
    try:
        return widgets.deals_payload(db)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=503, detail=f"deal feeds unavailable: {exc}") from exc
