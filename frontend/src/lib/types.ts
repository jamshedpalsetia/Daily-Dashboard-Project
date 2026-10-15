export type Priority = "low" | "medium" | "high";

export interface Condition {
  label: string;
  icon: string;
}

export interface ForecastDay {
  date: string;
  high: number | null;
  low: number | null;
  precip_chance: number | null;
  sunrise: string | null;
  sunset: string | null;
  condition: Condition;
}

export interface Weather {
  current: {
    temperature: number | null;
    feels_like: number | null;
    humidity: number | null;
    precipitation: number | null;
    wind_speed: number | null;
    condition: Condition;
    observed_at: string | null;
  };
  units: { temperature: string; wind_speed: string };
  forecast: ForecastDay[];
}

export interface WeatherResponse extends Envelope {
  weather: Weather;
  location: string;
}

export interface Envelope {
  stale: boolean;
  fetched_at: string;
  error: string | null;
}

export interface Quote {
  symbol: string;
  name: string | null;
  price: number | null;
  change: number | null;
  change_percent: number | null;
  volume: number | null;
  market_cap: number | null;
}

export interface MoversResponse extends Envelope {
  movers: {
    gainers: Quote[];
    losers: Quote[];
    actives: Quote[];
    errors: Record<string, string>;
  };
}

export interface Holding {
  id: number;
  symbol: string;
  shares: number | null;
  cost_basis: number | null;
  price: number | null;
  change: number | null;
  change_percent: number | null;
  currency: string;
  market_value: number | null;
  gain: number | null;
  gain_percent: number | null;
  day_change_value: number | null;
  error: string | null;
}

export interface WatchlistResponse extends Envelope {
  holdings: Holding[];
  totals?: {
    market_value: number | null;
    cost: number | null;
    gain: number | null;
    gain_percent: number | null;
    day_change: number | null;
  };
}

export interface Deal {
  title: string;
  link: string;
  summary: string;
  source: string;
  published_at: string | null;
}

export interface DealsResponse extends Envelope {
  deals: Deal[];
}

export interface NewsItem {
  title: string;
  link: string;
  summary: string;
  source: string;
  published_at: string | null;
}

export interface NewsResponse extends Envelope {
  news: {
    top: NewsItem[];
    business: NewsItem[];
    errors: Record<string, string>;
  };
}

export interface Todo {
  id: number;
  title: string;
  notes: string | null;
  priority: Priority;
  due_date: string | null;
  done: boolean;
  completed_at: string | null;
  created_at: string;
}

export interface AppSettings {
  location_label: string;
  latitude: number;
  longitude: number;
  timezone: string;
  units: "imperial" | "metric";
  email_to: string | null;
  digest_hour: number;
  digest_minute: number;
  digest_enabled: boolean;
  rss_feeds: string[];
  deal_keywords: string[];
  news_top_feeds: string[];
  news_business_feeds: string[];
}

export interface GeocodeResult {
  label: string;
  latitude: number;
  longitude: number;
  timezone: string;
  country_code: string;
}

export interface DigestStatus {
  smtp_configured: boolean;
  recent: {
    date: string;
    sent_at: string;
    trigger: string;
    status: string;
    detail: string | null;
  }[];
}
