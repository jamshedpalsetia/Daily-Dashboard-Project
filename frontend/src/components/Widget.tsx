import type { ReactNode } from "react";
import { relativeTime } from "../lib/format";

interface Props {
  title: string;
  subtitle?: string;
  isLoading?: boolean;
  error?: Error | null;
  stale?: boolean;
  fetchedAt?: string | null;
  actions?: ReactNode;
  children: ReactNode;
  rows?: number;
}

export function Widget({
  title,
  subtitle,
  isLoading,
  error,
  stale,
  fetchedAt,
  actions,
  children,
  rows = 4,
}: Props) {
  return (
    <section className="widget">
      <header className="widget-head">
        <div>
          <h2>{title}</h2>
          {subtitle && <p className="widget-sub">{subtitle}</p>}
        </div>
        <div className="widget-actions">
          {stale && <span className="badge badge-stale">stale</span>}
          {actions}
        </div>
      </header>

      <div className="widget-body">
        {isLoading ? (
          <div className="skeleton-stack">
            {Array.from({ length: rows }).map((_, i) => (
              <div key={i} className="skeleton" />
            ))}
          </div>
        ) : error ? (
          <p className="widget-error">{error.message}</p>
        ) : (
          children
        )}
      </div>

      {fetchedAt && !isLoading && !error && (
        <footer className="widget-foot">updated {relativeTime(fetchedAt)}</footer>
      )}
    </section>
  );
}
