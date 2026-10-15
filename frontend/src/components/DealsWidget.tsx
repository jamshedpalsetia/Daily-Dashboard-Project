import { useQuery } from "@tanstack/react-query";
import { api } from "../lib/api";
import { relativeTime } from "../lib/format";
import { Widget } from "./Widget";

export function DealsWidget() {
  const query = useQuery({
    queryKey: ["deals"],
    queryFn: api.deals,
    refetchInterval: 3 * 60 * 60 * 1000,
  });

  const deals = query.data?.deals ?? [];

  return (
    <Widget
      title="Travel Deals"
      subtitle="From your deal feeds"
      isLoading={query.isLoading}
      error={query.error as Error | null}
      stale={query.data?.stale}
      fetchedAt={query.data?.fetched_at}
      rows={5}
    >
      {deals.length === 0 ? (
        <p className="empty">No deals matched your feeds and keywords.</p>
      ) : (
        <ul className="deals">
          {deals.map((deal) => (
            <li key={deal.link}>
              <a href={deal.link} target="_blank" rel="noreferrer">
                {deal.title}
              </a>
              <div className="deal-meta">
                {deal.source}
                {deal.published_at ? ` · ${relativeTime(deal.published_at)}` : ""}
              </div>
            </li>
          ))}
        </ul>
      )}
    </Widget>
  );
}
