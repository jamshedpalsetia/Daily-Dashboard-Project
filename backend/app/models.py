from __future__ import annotations

import datetime as dt
import enum

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum,
    Float,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base

DEFAULT_RSS_FEEDS = [
    "https://www.theflightdeal.com/feed/",
    "https://www.fly4free.com/feed/",
    # Secret Flying's own /feed/ redirects to the homepage; FeedBurner is the
    # only endpoint that still returns RSS.
    "https://feeds.feedburner.com/SecretFlying",
]

# Google News aggregates across publishers, so a single feed per section gives
# a reasonable spread without needing an API key.
DEFAULT_NEWS_TOP_FEEDS = [
    "https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en",
]

DEFAULT_NEWS_BUSINESS_FEEDS = [
    "https://news.google.com/rss/headlines/section/topic/BUSINESS?hl=en-US&gl=US&ceid=US:en",
]


class Priority(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"


class AppSettings(Base):
    """Single-row table holding every user-editable preference."""

    __tablename__ = "settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    location_label: Mapped[str] = mapped_column(String(120), default="San Francisco, US")
    latitude: Mapped[float] = mapped_column(Float, default=37.7749)
    longitude: Mapped[float] = mapped_column(Float, default=-122.4194)
    timezone: Mapped[str] = mapped_column(String(64), default="America/Los_Angeles")
    units: Mapped[str] = mapped_column(String(16), default="imperial")

    email_to: Mapped[str | None] = mapped_column(String(255), nullable=True)
    digest_hour: Mapped[int] = mapped_column(Integer, default=7)
    digest_minute: Mapped[int] = mapped_column(Integer, default=0)
    digest_enabled: Mapped[bool] = mapped_column(Boolean, default=True)

    rss_feeds: Mapped[list] = mapped_column(JSONB, default=list)
    deal_keywords: Mapped[list] = mapped_column(JSONB, default=list)
    news_top_feeds: Mapped[list] = mapped_column(JSONB, default=list)
    news_business_feeds: Mapped[list] = mapped_column(JSONB, default=list)

    updated_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class WatchlistItem(Base):
    __tablename__ = "watchlist_item"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    symbol: Mapped[str] = mapped_column(String(16), unique=True, index=True)
    shares: Mapped[float | None] = mapped_column(Float, nullable=True)
    cost_basis: Mapped[float | None] = mapped_column(Float, nullable=True)
    added_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class Todo(Base):
    __tablename__ = "todo"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(500))
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    priority: Mapped[Priority] = mapped_column(
        Enum(Priority, name="priority"), default=Priority.medium
    )
    due_date: Mapped[dt.date | None] = mapped_column(Date, nullable=True)
    done: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    completed_at: Mapped[dt.datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class CacheEntry(Base):
    __tablename__ = "cache_entry"

    key: Mapped[str] = mapped_column(String(255), primary_key=True)
    payload: Mapped[dict] = mapped_column(JSONB)
    fetched_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    expires_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True))


class DigestLog(Base):
    __tablename__ = "digest_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    sent_for_date: Mapped[dt.date] = mapped_column(Date, index=True)
    sent_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    # "scheduled" rows are what the cron dedupe checks against; manual sends
    # from the UI are logged too but never block the daily run.
    trigger: Mapped[str] = mapped_column(String(16), default="scheduled")
    status: Mapped[str] = mapped_column(String(32), default="sent")
    detail: Mapped[str | None] = mapped_column(Text, nullable=True)
