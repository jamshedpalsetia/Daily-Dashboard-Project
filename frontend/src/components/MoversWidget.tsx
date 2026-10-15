import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { api } from "../lib/api";
import { compact, money, percent } from "../lib/format";
import type { Quote } from "../lib/types";
import { TickerLink } from "./TickerLink";
import { Widget } from "./Widget";

const TABS = [
  { id: "gainers", label: "Gainers" },
  { id: "losers", label: "Losers" },
  { id: "actives", label: "Active" },
] as const;

type TabId = (typeof TABS)[number]["id"];

export function MoversWidget() {
  const [tab, setTab] = useState<TabId>("gainers");
  const query = useQuery({
    queryKey: ["movers"],
    queryFn: api.movers,
    refetchInterval: 10 * 60 * 1000,
  });

  const rows: Quote[] = query.data?.movers?.[tab] ?? [];

  return (
    <Widget
      title="Market Movers"
      subtitle="US equities"
      isLoading={query.isLoading}
      error={query.error as Error | null}
      stale={query.data?.stale}
      fetchedAt={query.data?.fetched_at}
      actions={
        <div className="tabs">
          {TABS.map((t) => (
            <button
              key={t.id}
              className={t.id === tab ? "tab tab-active" : "tab"}
              onClick={() => setTab(t.id)}
            >
              {t.label}
            </button>
          ))}
        </div>
      }
    >
      {rows.length === 0 ? (
        <p className="empty">No data for this screen right now.</p>
      ) : (
        <table className="table">
          <tbody>
            {rows.map((q) => (
              <tr key={q.symbol}>
                <td className="sym">
                  <TickerLink symbol={q.symbol} />
                </td>
                <td className="name">{q.name}</td>
                <td className="num">{money(q.price)}</td>
                <td className={`num ${(q.change_percent ?? 0) >= 0 ? "up" : "down"}`}>
                  {percent(q.change_percent)}
                </td>
                <td className="num muted">{compact(q.volume)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </Widget>
  );
}
