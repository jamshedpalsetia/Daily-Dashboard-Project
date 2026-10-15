from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    DEFAULT_NEWS_BUSINESS_FEEDS,
    DEFAULT_NEWS_TOP_FEEDS,
    DEFAULT_RSS_FEEDS,
    AppSettings,
)


def get_settings_row(db: Session) -> AppSettings:
    """The app is single-user, so there is exactly one settings row.

    The migration seeds it; this recreates it if the row is ever deleted so the
    dashboard can't get stuck on a missing-config error.
    """
    row = db.scalars(select(AppSettings).order_by(AppSettings.id).limit(1)).first()
    if row is None:
        row = AppSettings(
            id=1,
            rss_feeds=list(DEFAULT_RSS_FEEDS),
            deal_keywords=[],
            news_top_feeds=list(DEFAULT_NEWS_TOP_FEEDS),
            news_business_feeds=list(DEFAULT_NEWS_BUSINESS_FEEDS),
        )
        db.add(row)
        db.commit()
        db.refresh(row)
    return row
