from __future__ import annotations

import logging

import yfinance as yf

log = logging.getLogger(__name__)

SCREENS = {
    "gainers": "day_gainers",
    "losers": "day_losers",
    "actives": "most_actives",
}


def _num(value) -> float | None:
    try:
        if value is None:
            return None
        out = float(value)
    except (TypeError, ValueError):
        return None
    return out if out == out else None  # filter NaN


def _quote_from_screen(row: dict) -> dict:
    return {
        "symbol": row.get("symbol"),
        "name": row.get("shortName") or row.get("displayName") or row.get("longName"),
        "price": _num(row.get("regularMarketPrice")),
        "change": _num(row.get("regularMarketChange")),
        "change_percent": _num(row.get("regularMarketChangePercent")),
        "volume": _num(row.get("regularMarketVolume")),
        "market_cap": _num(row.get("marketCap")),
    }


def fetch_movers(count: int = 8) -> dict:
    """Top gainers, losers and most-active US equities.

    These come from Yahoo's unofficial screener endpoints, so a failure here is
    expected occasionally and is handled by the caching layer.
    """
    out: dict[str, list[dict]] = {}
    errors: dict[str, str] = {}

    for label, screen_id in SCREENS.items():
        try:
            response = yf.screen(screen_id, count=count)
            quotes = (response or {}).get("quotes", []) or []
            out[label] = [_quote_from_screen(q) for q in quotes[:count]]
        except Exception as exc:  # noqa: BLE001 - one dead screen shouldn't kill the rest
            log.warning("screener %s failed: %s", screen_id, exc)
            out[label] = []
            errors[label] = str(exc)

    if all(not v for v in out.values()):
        raise RuntimeError(f"all screeners failed: {errors}")

    out["errors"] = errors
    return out


def _fast_info_value(info, *keys):
    """Read a fast_info field across yfinance versions.

    yfinance switched fast_info keys from snake_case to camelCase, and the old
    aliases now silently return None rather than raising, so try both spellings.
    """
    for key in keys:
        try:
            value = info.get(key) if hasattr(info, "get") else getattr(info, key, None)
        except Exception:  # noqa: BLE001
            continue
        if value is not None:
            return value
    return None


def fetch_quotes(symbols: list[str]) -> dict[str, dict]:
    """Current price and day change for each watchlist symbol."""
    results: dict[str, dict] = {}
    for symbol in symbols:
        try:
            info = yf.Ticker(symbol).fast_info
            last = _num(_fast_info_value(info, "lastPrice", "last_price"))
            prev = _num(_fast_info_value(info, "previousClose", "previous_close"))
            currency = _fast_info_value(info, "currency")

            change = None
            change_percent = None
            if last is not None and prev:
                change = last - prev
                change_percent = (change / prev) * 100

            results[symbol] = {
                "symbol": symbol,
                "price": last,
                "previous_close": prev,
                "change": change,
                "change_percent": change_percent,
                "currency": currency or "USD",
                "error": None if last is not None else "no price returned",
            }
        except Exception as exc:  # noqa: BLE001 - per-symbol isolation
            log.warning("quote for %s failed: %s", symbol, exc)
            results[symbol] = {
                "symbol": symbol,
                "price": None,
                "previous_close": None,
                "change": None,
                "change_percent": None,
                "currency": "USD",
                "error": str(exc),
            }
    return results


def validate_symbol(symbol: str) -> bool:
    """Cheap existence check used before adding to the watchlist."""
    try:
        info = yf.Ticker(symbol).fast_info
        price = _fast_info_value(info, "lastPrice", "last_price")
        return _num(price) is not None
    except Exception:  # noqa: BLE001
        return False
