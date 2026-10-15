from __future__ import annotations

from app.providers.rss import fetch_entries


def fetch_deals(
    feeds: list[str],
    keywords: list[str] | None = None,
    limit: int = 12,
    max_age_days: int = 14,
) -> list[dict]:
    """Travel-deal headlines. Deals stay relevant for a while, hence the long
    max_age_days compared with news."""
    return fetch_entries(
        feeds, keywords=keywords, limit=limit, max_age_days=max_age_days
    )
