import { useQuery } from "@tanstack/react-query";
import { api } from "../lib/api";
import { relativeTime } from "../lib/format";
import type { NewsItem } from "../lib/types";
import { Widget } from "./Widget";

const SECTIONS = [
  { id: "top", label: "Top Headlines" },
  { id: "business", label: "Business" },
] as const;

function Story({ item }: { item: NewsItem }) {
  return (
    <li>
      <a href={item.link} target="_blank" rel="noreferrer">
        {item.title}
      </a>
      <div className="deal-meta">
        {item.source}
        {item.published_at ? ` · ${relativeTime(item.published_at)}` : ""}
      </div>
    </li>
  );
}

export function NewsWidget() {
  const query = useQuery({
    queryKey: ["news"],
    queryFn: api.news,
    refetchInterval: 20 * 60 * 1000,
  });

  const news = query.data?.news;

  return (
    <Widget
      title="News"
      subtitle="Today's headlines"
      isLoading={query.isLoading}
      error={query.error as Error | null}
      stale={query.data?.stale}
      fetchedAt={query.data?.fetched_at}
      rows={6}
    >
      {news &&
        SECTIONS.map(({ id, label }) => (
          <div key={id} className="news-section">
            <h3 className="news-heading">{label}</h3>
            {news[id].length === 0 ? (
              <p className="empty">Nothing available right now.</p>
            ) : (
              <ul className="deals">
                {news[id].map((item) => (
                  <Story key={item.link} item={item} />
                ))}
              </ul>
            )}
          </div>
        ))}
    </Widget>
  );
}
