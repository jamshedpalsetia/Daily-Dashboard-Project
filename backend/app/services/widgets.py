from __future__ import annotations

import datetime as dt
import hashlib

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models import Todo, WatchlistItem
from app.providers import news_rss, stocks_yfinance, travel_rss, weather_openmeteo
from app.services.cache import CachedResult, cached
from app.services.settings_service import get_settings_row

WEATHER_TTL = 30 * 60
MOVERS_TTL = 10 * 60
QUOTES_TTL = 5 * 60
DEALS_TTL = 3 * 60 * 60
NEWS_TTL = 20 * 60

NEWS_COUNT = 3

DONE_VISIBLE_DAYS = 3


def weather_payload(db: Session) -> dict:
    s = get_settings_row(db)
    key = f"weather:{s.latitude:.4f},{s.longitude:.4f}:{s.units}:{s.timezone}"
    result = cached(
        db,
        key,
        WEATHER_TTL,
        lambda: weather_openmeteo.fetch_weather(
            s.latitude, s.longitude, s.timezone, s.units
        ),
    )
    payload = result.as_response("weather")
    payload["location"] = s.location_label
    return payload


def movers_payload(db: Session) -> dict:
    result = cached(db, "stocks:movers", MOVERS_TTL, lambda: stocks_yfinance.fetch_movers(8))
    return result.as_response("movers")


def watchlist_payload(db: Session) -> dict:
    items = list(db.scalars(select(WatchlistItem).order_by(WatchlistItem.symbol)))
    if not items:
        now = dt.datetime.now(dt.timezone.utc)
        return CachedResult(data=[], stale=False, fetched_at=now).as_response("holdings")

    symbols = [i.symbol for i in items]
    # Key on the symbol set so adding or removing a ticker refreshes immediately.
    digest = hashlib.sha1(",".join(symbols).encode()).hexdigest()[:12]
    result = cached(
        db, f"stocks:quotes:{digest}", QUOTES_TTL, lambda: stocks_yfinance.fetch_quotes(symbols)
    )
    quotes: dict = result.data or {}

    holdings = []
    total_value = 0.0
    total_cost = 0.0
    total_day_change = 0.0

    for item in items:
        quote = quotes.get(item.symbol, {})
        price = quote.get("price")
        change = quote.get("change")

        market_value = price * item.shares if price is not None and item.shares else None
        cost = item.cost_basis * item.shares if item.cost_basis and item.shares else None
        gain = market_value - cost if market_value is not None and cost is not None else None
        day_change_value = change * item.shares if change is not None and item.shares else None

        if market_value is not None:
            total_value += market_value
        if cost is not None:
            total_cost += cost
        if day_change_value is not None:
            total_day_change += day_change_value

        holdings.append(
            {
                "id": item.id,
                "symbol": item.symbol,
                "shares": item.shares,
                "cost_basis": item.cost_basis,
                "price": price,
                "change": change,
                "change_percent": quote.get("change_percent"),
                "currency": quote.get("currency", "USD"),
                "market_value": market_value,
                "gain": gain,
                "gain_percent": (gain / cost * 100) if gain is not None and cost else None,
                "day_change_value": day_change_value,
                "error": quote.get("error"),
            }
        )

    payload = result.as_response("holdings")
    payload["holdings"] = holdings
    payload["totals"] = {
        "market_value": total_value or None,
        "cost": total_cost or None,
        "gain": (total_value - total_cost) if total_cost else None,
        "gain_percent": ((total_value - total_cost) / total_cost * 100) if total_cost else None,
        "day_change": total_day_change or None,
    }
    return payload


def deals_payload(db: Session) -> dict:
    s = get_settings_row(db)
    feeds = list(s.rss_feeds or [])
    keywords = list(s.deal_keywords or [])
    if not feeds:
        now = dt.datetime.now(dt.timezone.utc)
        return CachedResult(data=[], stale=False, fetched_at=now).as_response("deals")

    digest = hashlib.sha1(("|".join(feeds) + "::" + "|".join(keywords)).encode()).hexdigest()[:12]
    result = cached(
        db,
        f"travel:deals:{digest}",
        DEALS_TTL,
        lambda: travel_rss.fetch_deals(feeds, keywords),
    )
    return result.as_response("deals")


def news_payload(db: Session) -> dict:
    s = get_settings_row(db)
    top = list(s.news_top_feeds or [])
    business = list(s.news_business_feeds or [])
    if not top and not business:
        now = dt.datetime.now(dt.timezone.utc)
        empty = {"top": [], "business": [], "errors": {}}
        return CachedResult(data=empty, stale=False, fetched_at=now).as_response("news")

    digest = hashlib.sha1(("|".join(top) + "::" + "|".join(business)).encode()).hexdigest()[:12]
    result = cached(
        db,
        f"news:{digest}",
        NEWS_TTL,
        lambda: news_rss.fetch_news(top, business, count=NEWS_COUNT),
    )
    return result.as_response("news")


def visible_todos(db: Session) -> list[Todo]:
    """Open todos plus anything completed within the last three days."""
    cutoff = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=DONE_VISIBLE_DAYS)
    stmt = (
        select(Todo)
        .where(
            or_(
                Todo.done.is_(False),
                Todo.completed_at.is_(None),
                Todo.completed_at > cutoff,
            )
        )
        .order_by(
            Todo.done.asc(),
            Todo.due_date.asc().nullslast(),
            Todo.created_at.desc(),
        )
    )
    return list(db.scalars(stmt))
