import type {
  AppSettings,
  DealsResponse,
  DigestStatus,
  GeocodeResult,
  MoversResponse,
  NewsResponse,
  Priority,
  Todo,
  WatchlistResponse,
  WeatherResponse,
} from "./types";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, {
    headers: init?.body ? { "Content-Type": "application/json" } : undefined,
    ...init,
  });

  if (!response.ok) {
    let detail = `${response.status} ${response.statusText}`;
    try {
      const body = await response.json();
      if (body?.detail) {
        detail = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail);
      }
    } catch {
      // Non-JSON error body; the status line is the best we have.
    }
    throw new Error(detail);
  }

  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

export const api = {
  weather: () => request<WeatherResponse>("/api/weather"),
  geocode: (q: string) =>
    request<{ results: GeocodeResult[] }>(`/api/weather/geocode?q=${encodeURIComponent(q)}`),

  movers: () => request<MoversResponse>("/api/stocks/movers"),
  watchlist: () => request<WatchlistResponse>("/api/stocks/watchlist"),
  addWatchlist: (body: { symbol: string; shares?: number | null; cost_basis?: number | null }) =>
    request<{ id: number; symbol: string }>("/api/stocks/watchlist", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  removeWatchlist: (id: number) =>
    request<void>(`/api/stocks/watchlist/${id}`, { method: "DELETE" }),

  deals: () => request<DealsResponse>("/api/travel/deals"),

  news: () => request<NewsResponse>("/api/news"),

  todos: () => request<Todo[]>("/api/todos"),
  addTodo: (body: {
    title: string;
    priority: Priority;
    due_date?: string | null;
    notes?: string | null;
  }) => request<Todo>("/api/todos", { method: "POST", body: JSON.stringify(body) }),
  updateTodo: (id: number, body: Partial<Pick<Todo, "title" | "priority" | "due_date" | "done" | "notes">>) =>
    request<Todo>(`/api/todos/${id}`, { method: "PATCH", body: JSON.stringify(body) }),
  deleteTodo: (id: number) => request<void>(`/api/todos/${id}`, { method: "DELETE" }),

  settings: () => request<AppSettings>("/api/settings"),
  updateSettings: (body: Partial<AppSettings>) =>
    request<AppSettings>("/api/settings", { method: "PATCH", body: JSON.stringify(body) }),

  digestStatus: () => request<DigestStatus>("/api/digest/status"),
  sendDigest: () => request<{ status: string }>("/api/digest/send-now", { method: "POST" }),
};
