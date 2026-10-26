import { COLORS, LEVELS, fmtDuration } from "../risk";

/** Route summary cards + the corridor risk heat strip for the selected route. */
export function RouteCards({ plan, selectedRoute, onSelect }) {
  return (
    <div className="route-cards">
      {plan.routes.map((r) => {
        const s = r.summary;
        const total = r.distance_miles || 1;
        return (
          <button
            key={r.id}
            className={`route-card ${r.id === selectedRoute ? "active" : ""}`}
            onClick={() => onSelect(r.id)}
          >
            <div className="route-card-top">
              <span className="route-name">{r.name}</span>
              {r.recommended && <span className="badge-rec">★ Recommended</span>}
            </div>
            <div className="route-stats">
              <span>
                <b>{r.distance_miles.toLocaleString()}</b> mi
              </span>
              <span>
                <b>{fmtDuration(r.duration_min)}</b>
              </span>
              <span>
                Avg risk <b>{s.avg_risk}</b>
              </span>
            </div>
            <div className="risk-bar">
              {[
                [s.low_miles, 0],
                [s.moderate_miles, 1],
                [s.high_miles, 2],
                [s.severe_miles, 3],
                [s.no_travel_miles, 4],
              ]
                .filter(([miles]) => miles > 0)
                .map(([miles, level]) => (
                  <div
                    key={level}
                    className="risk-seg"
                    style={{
                      width: `${(miles / total) * 100}%`,
                      background: COLORS[level],
                    }}
                    title={`${LEVELS[level]}: ${miles} mi`}
                  />
                ))}
            </div>
            <div className="route-foot">
              {s.severe_miles > 0 && <span>🔴 {s.severe_miles} mi Severe</span>}
              {s.no_travel_miles > 0 && (
                <span>⛔ {s.no_travel_miles} mi No Travel</span>
              )}
              {s.high_miles > 0 && <span>🟠 {s.high_miles} mi High</span>}
              {s.severe_miles === 0 && s.no_travel_miles === 0 && (
                <span className="ok">✓ No Severe / No Travel stretches</span>
              )}
              <span className="worst">
                Worst: mile {s.worst_checkpoint.mile} ({s.worst_checkpoint.risk})
              </span>
            </div>
          </button>
        );
      })}
    </div>
  );
}

/** Clickable mile-by-mile risk strip for the selected route. */
export function HeatStrip({ route, selectedCheckpoint, onSelect }) {
  const total = route.distance_miles || 1;
  return (
    <div className="heat-strip-wrap">
      <div className="heat-strip-label">
        <span>Corridor risk heatmap (ETA weather)</span>
        <span>0 — {route.distance_miles.toLocaleString()} mi</span>
      </div>
      <div className="heat-strip">
        {route.checkpoints.map((cp, i) => {
          const next =
            i + 1 < route.checkpoints.length
              ? route.checkpoints[i + 1].mile
              : total;
          const width = Math.max(1.5, ((next - cp.mile) / total) * 100);
          return (
            <div
              key={i}
              className={`heat-seg ${
                selectedCheckpoint && selectedCheckpoint.mile === cp.mile
                  ? "sel"
                  : ""
              }`}
              style={{
                width: `${width}%`,
                background: COLORS[cp.risk_level],
              }}
              title={`Mile ${cp.mile} — ${LEVELS[cp.risk_level]}`}
              onClick={() => onSelect(cp)}
            />
          );
        })}
      </div>
    </div>
  );
}
