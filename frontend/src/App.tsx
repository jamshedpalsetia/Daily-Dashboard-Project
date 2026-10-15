import { useState } from "react";
import { DealsWidget } from "./components/DealsWidget";
import { MoversWidget } from "./components/MoversWidget";
import { NewsWidget } from "./components/NewsWidget";
import { SettingsDrawer } from "./components/SettingsDrawer";
import { TodoWidget } from "./components/TodoWidget";
import { WatchlistWidget } from "./components/WatchlistWidget";
import { WeatherWidget } from "./components/WeatherWidget";

export default function App() {
  const [settingsOpen, setSettingsOpen] = useState(false);
  const today = new Date().toLocaleDateString("en-US", {
    weekday: "long",
    month: "long",
    day: "numeric",
  });

  return (
    <div className="app">
      <header className="app-head">
        <div>
          <h1>Daily Dashboard</h1>
          <p className="app-date">{today}</p>
        </div>
        <button className="btn btn-secondary" onClick={() => setSettingsOpen(true)}>
          Settings
        </button>
      </header>

      <main className="grid">
        <WeatherWidget />
        <TodoWidget />
        <NewsWidget />
        <MoversWidget />
        <WatchlistWidget />
        <DealsWidget />
      </main>

      <SettingsDrawer open={settingsOpen} onClose={() => setSettingsOpen(false)} />
    </div>
  );
}
