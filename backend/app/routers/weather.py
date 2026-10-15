from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.providers import weather_openmeteo
from app.services import widgets

router = APIRouter(prefix="/api/weather", tags=["weather"])


@router.get("")
def read_weather(db: Session = Depends(get_db)) -> dict:
    try:
        return widgets.weather_payload(db)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=503, detail=f"weather unavailable: {exc}") from exc


@router.get("/geocode")
def geocode(q: str = Query(min_length=2)) -> dict:
    try:
        return {"results": weather_openmeteo.geocode(q)}
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=503, detail=f"geocoding unavailable: {exc}") from exc
