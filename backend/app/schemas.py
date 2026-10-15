from __future__ import annotations

import datetime as dt

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models import Priority


class SettingsOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    location_label: str
    latitude: float
    longitude: float
    timezone: str
    units: str
    email_to: str | None
    digest_hour: int
    digest_minute: int
    digest_enabled: bool
    rss_feeds: list[str]
    deal_keywords: list[str]
    news_top_feeds: list[str]
    news_business_feeds: list[str]


class SettingsUpdate(BaseModel):
    location_label: str | None = None
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    timezone: str | None = None
    units: str | None = None
    email_to: str | None = None
    digest_hour: int | None = Field(default=None, ge=0, le=23)
    digest_minute: int | None = Field(default=None, ge=0, le=59)
    digest_enabled: bool | None = None
    rss_feeds: list[str] | None = None
    deal_keywords: list[str] | None = None
    news_top_feeds: list[str] | None = None
    news_business_feeds: list[str] | None = None

    @field_validator("units")
    @classmethod
    def _units(cls, v: str | None) -> str | None:
        if v is not None and v not in {"imperial", "metric"}:
            raise ValueError("units must be 'imperial' or 'metric'")
        return v

    @field_validator("timezone")
    @classmethod
    def _timezone(cls, v: str | None) -> str | None:
        if v is None:
            return v
        from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

        try:
            ZoneInfo(v)
        except (ZoneInfoNotFoundError, ValueError) as exc:
            raise ValueError(f"unknown timezone: {v}") from exc
        return v


class WatchlistItemIn(BaseModel):
    symbol: str
    shares: float | None = Field(default=None, ge=0)
    cost_basis: float | None = Field(default=None, ge=0)

    @field_validator("symbol")
    @classmethod
    def _symbol(cls, v: str) -> str:
        cleaned = v.strip().upper()
        if not cleaned:
            raise ValueError("symbol is required")
        return cleaned


class WatchlistItemUpdate(BaseModel):
    shares: float | None = Field(default=None, ge=0)
    cost_basis: float | None = Field(default=None, ge=0)


class TodoIn(BaseModel):
    title: str
    notes: str | None = None
    priority: Priority = Priority.medium
    due_date: dt.date | None = None

    @field_validator("title")
    @classmethod
    def _title(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("title is required")
        return cleaned


class TodoUpdate(BaseModel):
    title: str | None = None
    notes: str | None = None
    priority: Priority | None = None
    due_date: dt.date | None = None
    done: bool | None = None


class TodoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    notes: str | None
    priority: Priority
    due_date: dt.date | None
    done: bool
    completed_at: dt.datetime | None
    created_at: dt.datetime
