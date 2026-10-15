import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { api } from "../lib/api";
import type { AppSettings, GeocodeResult } from "../lib/types";

interface Props {
  open: boolean;
  onClose: () => void;
}

const splitLines = (text: string) =>
  text
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean);

export function SettingsDrawer({ open, onClose }: Props) {
  const queryClient = useQueryClient();
  const settingsQuery = useQuery({ queryKey: ["settings"], queryFn: api.settings, enabled: open });
  const digestQuery = useQuery({
    queryKey: ["digest-status"],
    queryFn: api.digestStatus,
    enabled: open,
  });

  const [draft, setDraft] = useState<AppSettings | null>(null);
  const [placeQuery, setPlaceQuery] = useState("");
  const [places, setPlaces] = useState<GeocodeResult[]>([]);
  const [feedsText, setFeedsText] = useState("");
  const [keywordsText, setKeywordsText] = useState("");
  const [newsTopText, setNewsTopText] = useState("");
  const [newsBusinessText, setNewsBusinessText] = useState("");
  const [notice, setNotice] = useState<string | null>(null);

  useEffect(() => {
    if (settingsQuery.data) {
      setDraft(settingsQuery.data);
      setFeedsText(settingsQuery.data.rss_feeds.join("\n"));
      setKeywordsText(settingsQuery.data.deal_keywords.join(", "));
      setNewsTopText(settingsQuery.data.news_top_feeds.join("\n"));
      setNewsBusinessText(settingsQuery.data.news_business_feeds.join("\n"));
    }
  }, [settingsQuery.data]);

  const save = useMutation({
    mutationFn: api.updateSettings,
    onSuccess: () => {
      setNotice("Saved");
      // Location, units and feed changes invalidate the cached widget payloads.
      ["settings", "weather", "deals", "news"].forEach((key) =>
        queryClient.invalidateQueries({ queryKey: [key] }),
      );
      setTimeout(() => setNotice(null), 2500);
    },
    onError: (err: Error) => setNotice(err.message),
  });

  const search = useMutation({
    mutationFn: (q: string) => api.geocode(q),
    onSuccess: (data) => setPlaces(data.results),
  });

  const sendNow = useMutation({
    mutationFn: api.sendDigest,
    onSuccess: (data) => {
      setNotice(data.status === "sent" ? "Test email sent" : `Digest ${data.status}`);
      queryClient.invalidateQueries({ queryKey: ["digest-status"] });
    },
    onError: (err: Error) => setNotice(err.message),
  });

  if (!open) return null;

  const update = (patch: Partial<AppSettings>) =>
    setDraft((prev) => (prev ? { ...prev, ...patch } : prev));

  return (
    <div className="drawer-backdrop" onClick={onClose}>
      <aside className="drawer" onClick={(e) => e.stopPropagation()}>
        <header className="drawer-head">
          <h2>Settings</h2>
          <button className="icon-btn" onClick={onClose} aria-label="Close settings">
            ×
          </button>
        </header>

        {!draft ? (
          <p className="empty">Loading…</p>
        ) : (
          <div className="drawer-body">
            <fieldset>
              <legend>Location</legend>
              <p className="current">{draft.location_label}</p>
              <div className="row-form">
                <input
                  className="input input-grow"
                  placeholder="Search a city…"
                  value={placeQuery}
                  onChange={(e) => setPlaceQuery(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && placeQuery.length > 1) {
                      e.preventDefault();
                      search.mutate(placeQuery);
                    }
                  }}
                />
                <button
                  className="btn"
                  type="button"
                  onClick={() => placeQuery.length > 1 && search.mutate(placeQuery)}
                >
                  Search
                </button>
              </div>
              {places.length > 0 && (
                <ul className="place-list">
                  {places.map((p) => (
                    <li key={`${p.latitude},${p.longitude}`}>
                      <button
                        type="button"
                        onClick={() => {
                          update({
                            location_label: p.label,
                            latitude: p.latitude,
                            longitude: p.longitude,
                            timezone: p.timezone,
                          });
                          setPlaces([]);
                          setPlaceQuery("");
                        }}
                      >
                        {p.label}
                      </button>
                    </li>
                  ))}
                </ul>
              )}
              <label className="field">
                Units
                <select
                  value={draft.units}
                  onChange={(e) => update({ units: e.target.value as "imperial" | "metric" })}
                >
                  <option value="imperial">Fahrenheit / mph</option>
                  <option value="metric">Celsius / km/h</option>
                </select>
              </label>
              <label className="field">
                Timezone
                <input
                  value={draft.timezone}
                  onChange={(e) => update({ timezone: e.target.value })}
                />
              </label>
            </fieldset>

            <fieldset>
              <legend>Daily email</legend>
              <label className="field">
                Send to
                <input
                  type="email"
                  value={draft.email_to ?? ""}
                  placeholder="you@example.com"
                  onChange={(e) => update({ email_to: e.target.value })}
                />
              </label>
              <label className="field">
                Time
                <input
                  type="time"
                  value={`${String(draft.digest_hour).padStart(2, "0")}:${String(
                    draft.digest_minute,
                  ).padStart(2, "0")}`}
                  onChange={(e) => {
                    const [h, m] = e.target.value.split(":").map(Number);
                    update({ digest_hour: h, digest_minute: m });
                  }}
                />
              </label>
              <label className="field field-inline">
                <input
                  type="checkbox"
                  checked={draft.digest_enabled}
                  onChange={(e) => update({ digest_enabled: e.target.checked })}
                />
                Send the daily digest
              </label>

              {digestQuery.data && !digestQuery.data.smtp_configured && (
                <p className="form-error">
                  SMTP is not configured. Set SMTP_HOST / SMTP_FROM in your .env file.
                </p>
              )}

              <div className="row-form">
                <button
                  className="btn btn-secondary"
                  type="button"
                  onClick={() => sendNow.mutate()}
                  disabled={sendNow.isPending}
                >
                  {sendNow.isPending ? "Sending…" : "Send test email"}
                </button>
                <a className="btn btn-secondary" href="/api/digest/preview" target="_blank">
                  Preview
                </a>
              </div>

              {digestQuery.data?.recent?.length ? (
                <ul className="log">
                  {digestQuery.data.recent.map((r, i) => (
                    <li key={i}>
                      {r.date} · {r.trigger} ·{" "}
                      <span className={r.status === "sent" ? "up" : "down"}>{r.status}</span>
                      {r.detail ? ` — ${r.detail}` : ""}
                    </li>
                  ))}
                </ul>
              ) : null}
            </fieldset>

            <fieldset>
              <legend>Travel deal feeds</legend>
              <label className="field">
                RSS feeds (one per line)
                <textarea
                  rows={4}
                  value={feedsText}
                  onChange={(e) => setFeedsText(e.target.value)}
                />
              </label>
              <label className="field">
                Keyword filter (comma separated, blank shows everything)
                <input
                  value={keywordsText}
                  placeholder="SFO, Europe, Japan"
                  onChange={(e) => setKeywordsText(e.target.value)}
                />
              </label>
            </fieldset>

            <fieldset>
              <legend>News feeds</legend>
              <label className="field">
                Top headlines (one per line)
                <textarea
                  rows={3}
                  value={newsTopText}
                  onChange={(e) => setNewsTopText(e.target.value)}
                />
              </label>
              <label className="field">
                Business (one per line)
                <textarea
                  rows={3}
                  value={newsBusinessText}
                  onChange={(e) => setNewsBusinessText(e.target.value)}
                />
              </label>
            </fieldset>

            <div className="drawer-foot">
              {notice && <span className="notice">{notice}</span>}
              <button
                className="btn"
                disabled={save.isPending}
                onClick={() =>
                  save.mutate({
                    ...draft,
                    email_to: draft.email_to || null,
                    rss_feeds: splitLines(feedsText),
                    deal_keywords: keywordsText
                      .split(",")
                      .map((k) => k.trim())
                      .filter(Boolean),
                    news_top_feeds: splitLines(newsTopText),
                    news_business_feeds: splitLines(newsBusinessText),
                  })
                }
              >
                {save.isPending ? "Saving…" : "Save settings"}
              </button>
            </div>
          </div>
        )}
      </aside>
    </div>
  );
}
