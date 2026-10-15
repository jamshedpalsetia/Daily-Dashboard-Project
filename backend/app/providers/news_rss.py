from __future__ import annotations

import logging

from app.providers.rss import fetch_entries

log = logging.getLogger(__name__)

# News is only interesting while it's fresh.
MAX_AGE_DAYS = 2


def fetch_news(
    top_feeds: list[str],
    business_feeds: list[str],
    count: int = 3,
) -> dict:
    """Top headlines and business headlines, each trimmed to `count` items.

    Google News titles carry a " - Publisher" suffix that duplicates the source
    field, so it is stripped. One empty section is tolerated; both empty raises
    so the caching layer can fall back to the previous copy.
    """
    sections: dict[str, list[dict]] = {}
    errors: dict[str, str] = {}

    for label, feeds in (("top", top_feeds), ("business", business_feeds)):
        if not feeds:
            sections[label] = []
            continue
        try:
            sections[label] = fetch_entries(
                feeds,
                limit=count,
                max_age_days=MAX_AGE_DAYS,
                strip_source_suffix=True,
            )
        except Exception as exc:  # noqa: BLE001 - one dead section shouldn't kill the other
            log.warning("news section %s failed: %s", label, exc)
            sections[label] = []
            errors[label] = str(exc)

    if not sections["top"] and not sections["business"]:
        raise RuntimeError(f"no news available: {errors}")

    sections["errors"] = errors
    return sections
