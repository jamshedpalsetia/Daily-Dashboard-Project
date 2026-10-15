from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import scheduler
from app.db import get_db
from app.schemas import SettingsOut, SettingsUpdate
from app.services.settings_service import get_settings_row

router = APIRouter(prefix="/api/settings", tags=["settings"])

SCHEDULE_FIELDS = {"digest_hour", "digest_minute", "digest_enabled", "timezone"}


@router.get("", response_model=SettingsOut)
def read_settings(db: Session = Depends(get_db)) -> SettingsOut:
    return get_settings_row(db)


@router.patch("", response_model=SettingsOut)
def update_settings(payload: SettingsUpdate, db: Session = Depends(get_db)) -> SettingsOut:
    row = get_settings_row(db)
    fields = payload.model_dump(exclude_unset=True)

    for field, value in fields.items():
        setattr(row, field, value)
    db.commit()
    db.refresh(row)

    if SCHEDULE_FIELDS & fields.keys():
        scheduler.apply_digest_schedule()

    return row
