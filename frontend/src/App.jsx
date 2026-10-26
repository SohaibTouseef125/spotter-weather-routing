import { useMemo, useState } from "react";
import { fetchPlan } from "./api";
import { COLORS, LEVELS, checkpointRisk, fmtEta } from "./risk";
import MapView from "./components/MapView";
import { RouteCards, HeatStrip } from "./components/RouteCards";
import CheckpointPanel from "./components/CheckpointPanel";

function defaultDeparture() {
  const d = new Date(Date.now() + 60 * 60 * 1000);
  const pad = (n) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(
    d.getHours()
  )}:${pad(d.getMinutes())}`;
}

export default function App() {
  const [origin, setOrigin] = useState("Dallas");
  const [destination, setDestination] = useState("Houston");
  const [departure, setDeparture] = useState(defaultDeparture());
  const [loadLb, setLoadLb] = useState(35000);
  const [interval, setInterval] = useState(25);
  const [plan, setPlan] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [selectedRoute, setSelectedRoute] = useState(0);
  const [selectedCp, setSelectedCp] = useState(null);
  const [mode, setMode] = useState("eta"); // "eta" | "forecast"
  const [sliderHrs, setSliderHrs] = useState(0);

  async function planRoutes(e) {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      const data = await fetchPlan({
        origin,
        destination,
        departure: new Date(departure).toISOString(),
        loadLb: Number(loadLb),
        interval: Number(interval),
      });
      setPlan(data);
      setSelectedRoute(data.recommendation.route_id);
      setSelectedCp(null);
      setMode("eta");
      setSliderHrs(0);
    } catch (err) {
      setError(err.message);
    }
    setLoading(false);
  }

  // Current risk level for a checkpoint under the active view mode.
  function displayRisk(cp) {
    if (mode === "forecast" && cp.forecast) {
      const f = cp.forecast;
      return checkpointRisk(
        f.wind_mph[sliderHrs],
        f.rain_in_hr[sliderHrs],
        f.snow_in_hr[sliderHrs],
        plan.load_weight_lb
      ).level;
    }
    return cp.risk_level;
  }

  const route = plan ? plan.routes[selectedRoute] : null;
  const forecastTime = useMemo(() => {
    if (!plan) return "";
    return fmtEta(
      new Date(new Date(plan.departure).getTime() + sliderHrs * 3600 * 1000).toISOString()
    );
  }, [plan, sliderHrs]);

  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">
          <span className="brand-mark">🚚</span>
          <div>
            <h1>Weather-Aware Truck Routing</h1>
            <p>Spotter assessment · React + Django · OSRM + Open-Meteo</p>
          </div>
        </div>
        {plan && (
          <div className="topbar-rec">
            <span>Recommended:</span>
            <b>{plan.recommendation.route_name}</b>
          </div>
        )}
      </header>

      <div className="layout">
        <aside className="sidebar">
          <form className="form" onSubmit={planRoutes}>
            <label>
              Origin
              <input
                value={origin}
                onChange={(e) => setOrigin(e.target.value)}
                placeholder="e.g. Dallas"
                required
              />
            </label>
            <label>
              Destination
              <input
                value={destination}
                onChange={(e) => setDestination(e.target.value)}
                placeholder="e.g. Houston"
                required
              />
            </label>
            <div className="form-row">
              <label>
                Departure
                <input
                  type="datetime-local"
                  value={departure}
                  onChange={(e) => setDeparture(e.target.value)}
                  required
                />
              </label>
              <label>
                Load weight (lb)
                <input
                  type="number"
                  min="0"
                  max="100000"
                  value={loadLb}
                  onChange={(e) => setLoadLb(e.target.value)}
                  required
                />
              </label>
            </div>
            <label>
              Weather sample interval
              <select
                value={interval}
                onChange={(e) => setInterval(e.target.value)}
              >
                <option value={10}>Every 10 miles</option>
                <option value={25}>Every 25 miles</option>
                <option value={50}>Every 50 miles</option>
              </select>
            </label>
            <button className="btn-primary" type="submit" disabled={loading}>
              {loading ? "Planning routes…" : "Plan routes"}
            </button>
            {error && <p className="error">{error}</p>}
          </form>

          {plan && (
            <>
              <p className="rec-note">{plan.recommendation.reason}</p>
              <RouteCards
                plan={plan}
                selectedRoute={selectedRoute}
                onSelect={(id) => {
                  setSelectedRoute(id);
                  setSelectedCp(null);
                }}
              />
              <HeatStrip
                route={route}
                selectedCheckpoint={selectedCp}
                onSelect={setSelectedCp}
              />
              <CheckpointPanel
                cp={selectedCp}
                loadLb={plan.load_weight_lb}
                onClose={() => setSelectedCp(null)}
              />
              <div className="legend">
                <b>Risk legend</b>
                <div>
                  {LEVELS.map((name, i) => (
                    <span key={i}>
                      <i style={{ background: COLORS[i] }} />
                      {name}
                    </span>
                  ))}
                </div>
                <p>
                  Risk uses wind / rain / snow rates at each checkpoint's ETA,
                  plus load rules (≥55 mph = No Travel; 45–54 mph with
                  &gt;30,000 lb = No Travel; 35–44 mph with &gt;40,000 lb =
                  Severe).
                </p>
              </div>
            </>
          )}
        </aside>

        <main className="map-area">
          {plan ? (
            <>
              <MapView
                plan={plan}
                selectedRoute={selectedRoute}
                selectedCheckpoint={selectedCp}
                onSelectCheckpoint={setSelectedCp}
                displayRisk={displayRisk}
              />
              <div className="slider-card">
                <div className="slider-tabs">
                  <button
                    className={mode === "eta" ? "active" : ""}
                    onClick={() => setMode("eta")}
                  >
                    ETA weather
                  </button>
                  <button
                    className={mode === "forecast" ? "active" : ""}
                    onClick={() => setMode("forecast")}
                  >
                    Forecast slider
                  </button>
                </div>
                {mode === "forecast" ? (
                  <>
                    <input
                      type="range"
                      min="0"
                      max="48"
                      value={sliderHrs}
                      onChange={(e) => setSliderHrs(Number(e.target.value))}
                    />
                    <div className="slider-meta">
                      <span>
                        Departure +{sliderHrs}h · {forecastTime}
                      </span>
                      <span>Checkpoint colours update instantly</span>
                    </div>
                  </>
                ) : (
                  <p className="slider-meta">
                    Checkpoints coloured by weather at the truck's estimated
                    arrival time. Click any checkpoint for details.
                  </p>
                )}
              </div>
            </>
          ) : (
            <div className="map-empty">
              <h2>Plan your safest route</h2>
              <p>
                Enter an origin, destination, departure time and load weight —
                the app compares up to 3 routes, checks the weather at every
                checkpoint along the way, and recommends the safest one.
              </p>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
