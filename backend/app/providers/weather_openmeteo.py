from __future__ import annotations

import httpx

FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"

TIMEOUT = httpx.Timeout(12.0)

# WMO weather interpretation codes.
WMO_CODES: dict[int, tuple[str, str]] = {
    0: ("Clear sky", "sun"),
    1: ("Mainly clear", "sun"),
    2: ("Partly cloudy", "cloud-sun"),
    3: ("Overcast", "cloud"),
    45: ("Fog", "fog"),
    48: ("Depositing rime fog", "fog"),
    51: ("Light drizzle", "drizzle"),
    53: ("Moderate drizzle", "drizzle"),
    55: ("Dense drizzle", "drizzle"),
    56: ("Light freezing drizzle", "sleet"),
    57: ("Dense freezing drizzle", "sleet"),
    61: ("Slight rain", "rain"),
    63: ("Moderate rain", "rain"),
    65: ("Heavy rain", "rain"),
    66: ("Light freezing rain", "sleet"),
    67: ("Heavy freezing rain", "sleet"),
    71: ("Slight snow", "snow"),
    73: ("Moderate snow", "snow"),
    75: ("Heavy snow", "snow"),
    77: ("Snow grains", "snow"),
    80: ("Slight rain showers", "rain"),
    81: ("Moderate rain showers", "rain"),
    82: ("Violent rain showers", "rain"),
    85: ("Slight snow showers", "snow"),
    86: ("Heavy snow showers", "snow"),
    95: ("Thunderstorm", "thunder"),
    96: ("Thunderstorm with slight hail", "thunder"),
    99: ("Thunderstorm with heavy hail", "thunder"),
}


def describe(code: int | None) -> dict[str, str]:
    label, icon = WMO_CODES.get(code if code is not None else -1, ("Unknown", "cloud"))
    return {"label": label, "icon": icon}


def fetch_weather(
    latitude: float,
    longitude: float,
    timezone: str,
    units: str = "imperial",
) -> dict:
    imperial = units == "imperial"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "timezone": timezone or "auto",
        "forecast_days": 5,
        "current": ",".join(
            [
                "temperature_2m",
                "relative_humidity_2m",
                "apparent_temperature",
                "precipitation",
                "weather_code",
                "wind_speed_10m",
            ]
        ),
        "daily": ",".join(
            [
                "weather_code",
                "temperature_2m_max",
                "temperature_2m_min",
                "precipitation_probability_max",
                "sunrise",
                "sunset",
            ]
        ),
        "temperature_unit": "fahrenheit" if imperial else "celsius",
        "wind_speed_unit": "mph" if imperial else "kmh",
        "precipitation_unit": "inch" if imperial else "mm",
    }

    with httpx.Client(timeout=TIMEOUT) as client:
        resp = client.get(FORECAST_URL, params=params)
        resp.raise_for_status()
        raw = resp.json()

    current = raw.get("current", {})
    current_units = raw.get("current_units", {})
    daily = raw.get("daily", {})

    forecast = []
    for i, day in enumerate(daily.get("time", [])):
        forecast.append(
            {
                "date": day,
                "high": daily.get("temperature_2m_max", [None] * (i + 1))[i],
                "low": daily.get("temperature_2m_min", [None] * (i + 1))[i],
                "precip_chance": daily.get("precipitation_probability_max", [None] * (i + 1))[i],
                "sunrise": daily.get("sunrise", [None] * (i + 1))[i],
                "sunset": daily.get("sunset", [None] * (i + 1))[i],
                "condition": describe(daily.get("weather_code", [None] * (i + 1))[i]),
            }
        )

    # Open-Meteo labels imperial wind speed "mp/h"; everyone writes "mph".
    wind_unit = current_units.get("wind_speed_10m", "mph" if imperial else "km/h")
    if wind_unit == "mp/h":
        wind_unit = "mph"

    return {
        "current": {
            "temperature": current.get("temperature_2m"),
            "feels_like": current.get("apparent_temperature"),
            "humidity": current.get("relative_humidity_2m"),
            "precipitation": current.get("precipitation"),
            "wind_speed": current.get("wind_speed_10m"),
            "condition": describe(current.get("weather_code")),
            "observed_at": current.get("time"),
        },
        "units": {
            "temperature": current_units.get("temperature_2m", "°F" if imperial else "°C"),
            "wind_speed": wind_unit,
        },
        "forecast": forecast,
    }


def geocode(query: str, count: int = 5) -> list[dict]:
    """Turn a typed city name into coordinates for the settings panel."""
    with httpx.Client(timeout=TIMEOUT) as client:
        resp = client.get(
            GEOCODE_URL,
            params={"name": query, "count": count, "language": "en", "format": "json"},
        )
        resp.raise_for_status()
        raw = resp.json()

    results = []
    for item in raw.get("results", []) or []:
        parts = [item.get("name"), item.get("admin1"), item.get("country")]
        results.append(
            {
                "label": ", ".join(p for p in parts if p),
                "latitude": item.get("latitude"),
                "longitude": item.get("longitude"),
                "timezone": item.get("timezone"),
                "country_code": item.get("country_code"),
            }
        )
    return results
