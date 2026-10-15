export function money(value: number | null | undefined, currency = "USD"): string {
  if (value === null || value === undefined) return "—";
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency,
    maximumFractionDigits: Math.abs(value) >= 1000 ? 0 : 2,
  }).format(value);
}

export function percent(value: number | null | undefined): string {
  if (value === null || value === undefined) return "—";
  return `${value >= 0 ? "+" : ""}${value.toFixed(2)}%`;
}

export function signed(value: number | null | undefined): string {
  if (value === null || value === undefined) return "—";
  return `${value >= 0 ? "+" : "-"}${money(Math.abs(value))}`;
}

export function compact(value: number | null | undefined): string {
  if (value === null || value === undefined) return "—";
  return new Intl.NumberFormat("en-US", { notation: "compact" }).format(value);
}

export function temp(value: number | null | undefined, unit: string): string {
  if (value === null || value === undefined) return "—";
  return `${Math.round(value)}${unit}`;
}

export function weekday(isoDate: string): string {
  // Parsed as local noon so a date-only string can't slip to the previous day.
  const date = new Date(`${isoDate}T12:00:00`);
  return date.toLocaleDateString("en-US", { weekday: "short" });
}

export function shortDate(isoDate: string): string {
  const date = new Date(`${isoDate}T12:00:00`);
  return date.toLocaleDateString("en-US", { month: "short", day: "numeric" });
}

export function relativeTime(iso: string | null): string {
  if (!iso) return "";
  const then = new Date(iso).getTime();
  const minutes = Math.round((Date.now() - then) / 60000);
  if (minutes < 1) return "just now";
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.round(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  return `${Math.round(hours / 24)}d ago`;
}

export function todayISO(): string {
  const now = new Date();
  const offset = now.getTimezoneOffset() * 60000;
  return new Date(now.getTime() - offset).toISOString().slice(0, 10);
}
