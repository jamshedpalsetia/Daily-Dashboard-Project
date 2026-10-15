import { useQuery } from "@tanstack/react-query";
import { api } from "../lib/api";
import { temp, weekday } from "../lib/format";
import { Widget } from "./Widget";

const ICONS: Record<string, string> = {
  sun: "☀️",
  "cloud-sun": "⛅",
  cloud: "☁️",
  fog: "🌫️",
  drizzle: "🌦️",
  rain: "🌧️",
  sleet: "🌨️",
  snow: "❄️",
  thunder: "⛈️",
};

export function WeatherWidget() {
  const query = useQuery({
    queryKey: ["weather"],
    queryFn: api.weather,
    refetchInterval: 30 * 60 * 1000,
  });

  const data = query.data;
  const current = data?.weather.current;
  const units = data?.weather.units;

  return (
    <Widget
      title="Weather"
      subtitle={data?.location}
      isLoading={query.isLoading}
      error={query.error as Error | null}
      stale={data?.stale}
      fetchedAt={data?.fetched_at}
      rows={3}
    >
      {current && units && (
        <>
          <div className="weather-now">
            <span className="weather-icon">{ICONS[current.condition.icon] ?? "☁️"}</span>
            <div>
              <div className="weather-temp">{temp(current.temperature, units.temperature)}</div>
              <div className="weather-label">{current.condition.label}</div>
              <div className="weather-meta">
                Feels {temp(current.feels_like, units.temperature)} · Wind{" "}
                {Math.round(current.wind_speed ?? 0)} {units.wind_speed} · Humidity{" "}
                {current.humidity ?? "—"}%
              </div>
            </div>
          </div>

          <div className="forecast">
            {data.weather.forecast.map((day) => (
              <div key={day.date} className="forecast-day">
                <span className="forecast-name">{weekday(day.date)}</span>
                <span className="forecast-icon">{ICONS[day.condition.icon] ?? "☁️"}</span>
                <span className="forecast-temps">
                  <strong>{temp(day.high, "°")}</strong>
                  <span className="muted">{temp(day.low, "°")}</span>
                </span>
                <span className="forecast-precip">
                  {day.precip_chance ? `${day.precip_chance}%` : ""}
                </span>
              </div>
            ))}
          </div>
        </>
      )}
    </Widget>
  );
}
