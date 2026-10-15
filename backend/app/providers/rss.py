from __future__ import annotations

import datetime as dt
import logging
import re
from html import unescape

import feedparser
import httpx

log = logging.getLogger(__name__)

TIMEOUT = httpx.Timeout(15.0)
USER_AGENT = "DailyDashboard/1.0 (+personal use)"
TAG_RE = re.compile(r"<[^>]+>")

# Google News titles arrive as "Headline - Publisher"; the publisher is also
# available separately, so strip the duplicated suffix.
GOOGLE_SUFFIX_RE = re.compile(r"\s+-\s+[^-]{2,40}$")


def clean(text: str | None, limit: int = 260) -> str:
    if not text:
        return ""
    stripped = unescape(TAG_RE.sub(" ", text))
    collapsed = " ".join(stripped.split())
    return collapsed[: limit - 1] + "\u2026" if len(collapsed) > limit else collapsed


def published_at(entry) -> dt.datetime | None:
    for attr in ("published_parsed", "updated_parsed"):
        parsed = getattr(entry, attr, None)
        if parsed:
            try:
                return dt.datetime(*parsed[:6], tzinfo=dt.timezone.utc)
            except (TypeError, ValueError):
                continue
    return None


def matches(text: str, keywords: list[str]) -> bool:
    if not keywords:
        return True
    lowered = text.lower()
    return any(k.strip().lower() in lowered for k in keywords if k.strip())


def _source(entry, feed_title: str) -> str:
    # Google News nests the originating publisher under entry.source.
    source = getattr(entry, "source", None)
    if source is not None:
        title = source.get("title") if hasattr(source, "get") else getattr(source, "title", None)
        if title:
            return clean(title, 60)
    return feed_title


def fetch_entries(
    feeds: list[str],
    keywords: list[str] | None = None,
    limit: int = 12,
    max_age_days: int = 14,
    strip_source_suffix: bool = False,
) -> list[dict]:
    """Aggregate and normalise entries from a list of RSS feeds.

    feedparser is handed already-downloaded bytes so we control timeouts and the
    user agent; several publishers reject the default urllib agent. One bad feed
    is logged and skipped; only an all-empty result raises.
    """
    keywords = keywords or []
    cutoff = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=max_age_days)
    seen_links: set[str] = set()
    seen_titles: set[str] = set()
    items: list[dict] = []
    errors: list[str] = []

    with httpx.Client(
        timeout=TIMEOUT, follow_redirects=True, headers={"User-Agent": USER_AGENT}
    ) as client:
        for feed_url in feeds:
            try:
                resp = client.get(feed_url)
                resp.raise_for_status()
                parsed = feedparser.parse(resp.content)
            except Exception as exc:  # noqa: BLE001 - one bad feed shouldn't kill the widget
                log.warning("feed %s failed: %s", feed_url, exc)
                errors.append(f"{feed_url}: {exc}")
                continue

            feed_title = clean(getattr(parsed.feed, "title", ""), 60) or feed_url

            for entry in parsed.entries:
                link = getattr(entry, "link", None)
                title = clean(getattr(entry, "title", ""), 200)
                if not link or not title or link in seen_links:
                    continue

                when = published_at(entry)
                if when and when < cutoff:
                    continue

                summary = clean(
                    getattr(entry, "summary", None) or getattr(entry, "description", None)
                )
                if not matches(f"{title} {summary}", keywords):
                    continue

                source = _source(entry, feed_title)
                if strip_source_suffix:
                    title = GOOGLE_SUFFIX_RE.sub("", title) or title

                # Aggregators repeat the same story from several publishers.
                title_key = title.lower()
                if title_key in seen_titles:
                    continue

                seen_links.add(link)
                seen_titles.add(title_key)
                items.append(
                    {
                        "title": title,
                        "link": link,
                        "summary": summary,
                        "source": source,
                        "published_at": when.isoformat() if when else None,
                    }
                )

    if not items and errors:
        raise RuntimeError("; ".join(errors[:3]))

    # Undated entries sort last rather than pretending to be brand new.
    items.sort(key=lambda i: i["published_at"] or "", reverse=True)
    return items[:limit]
