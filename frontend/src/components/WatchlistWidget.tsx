import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { api } from "../lib/api";
import { money, percent, signed } from "../lib/format";
import { TickerLink } from "./TickerLink";
import { Widget } from "./Widget";

export function WatchlistWidget() {
  const queryClient = useQueryClient();
  const [symbol, setSymbol] = useState("");
  const [shares, setShares] = useState("");
  const [costBasis, setCostBasis] = useState("");
  const [formError, setFormError] = useState<string | null>(null);

  const query = useQuery({
    queryKey: ["watchlist"],
    queryFn: api.watchlist,
    refetchInterval: 5 * 60 * 1000,
  });

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ["watchlist"] });

  const add = useMutation({
    mutationFn: api.addWatchlist,
    onSuccess: () => {
      setSymbol("");
      setShares("");
      setCostBasis("");
      setFormError(null);
      invalidate();
    },
    onError: (err: Error) => setFormError(err.message),
  });

  const remove = useMutation({ mutationFn: api.removeWatchlist, onSuccess: invalidate });

  const totals = query.data?.totals;
  const holdings = query.data?.holdings ?? [];

  return (
    <Widget
      title="My Stocks"
      subtitle={
        totals?.market_value
          ? `${money(totals.market_value)} · ${signed(totals.day_change)} today`
          : "Personal watchlist"
      }
      isLoading={query.isLoading}
      error={query.error as Error | null}
      stale={query.data?.stale}
      fetchedAt={query.data?.fetched_at}
    >
      <form
        className="row-form"
        onSubmit={(e) => {
          e.preventDefault();
          if (!symbol.trim()) return;
          add.mutate({
            symbol: symbol.trim().toUpperCase(),
            shares: shares ? Number(shares) : null,
            cost_basis: costBasis ? Number(costBasis) : null,
          });
        }}
      >
        <input
          value={symbol}
          onChange={(e) => setSymbol(e.target.value)}
          placeholder="Symbol"
          className="input input-sym"
          aria-label="Ticker symbol"
        />
        <input
          value={shares}
          onChange={(e) => setShares(e.target.value)}
          placeholder="Shares"
          type="number"
          step="any"
          min="0"
          className="input input-num"
          aria-label="Shares"
        />
        <input
          value={costBasis}
          onChange={(e) => setCostBasis(e.target.value)}
          placeholder="Cost"
          type="number"
          step="any"
          min="0"
          className="input input-num"
          aria-label="Cost basis per share"
        />
        <button className="btn" type="submit" disabled={add.isPending}>
          {add.isPending ? "…" : "Add"}
        </button>
      </form>
      {formError && <p className="form-error">{formError}</p>}

      {holdings.length === 0 ? (
        <p className="empty">Add a ticker to start tracking it.</p>
      ) : (
        <table className="table">
          <tbody>
            {holdings.map((h) => (
              <tr key={h.id}>
                <td className="sym">
                  <TickerLink symbol={h.symbol} />
                </td>
                <td className="num">{money(h.price, h.currency)}</td>
                <td className={`num ${(h.change_percent ?? 0) >= 0 ? "up" : "down"}`}>
                  {percent(h.change_percent)}
                </td>
                <td className="num muted">
                  {h.market_value !== null ? money(h.market_value, h.currency) : ""}
                </td>
                <td className={`num ${(h.gain ?? 0) >= 0 ? "up" : "down"}`}>
                  {h.gain !== null ? signed(h.gain) : ""}
                </td>
                <td className="actions-cell">
                  <button
                    className="icon-btn"
                    title={`Remove ${h.symbol}`}
                    aria-label={`Remove ${h.symbol}`}
                    onClick={() => remove.mutate(h.id)}
                  >
                    ×
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {typeof totals?.gain === "number" && (
        <p className="totals">
          Total return{" "}
          <span className={totals.gain >= 0 ? "up" : "down"}>
            {signed(totals.gain)} ({percent(totals.gain_percent)})
          </span>
        </p>
      )}
    </Widget>
  );
}
