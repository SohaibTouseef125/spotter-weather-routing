import { COLORS, LEVELS, fmtEta } from "../risk";

/** Detail panel for the clicked checkpoint (ETA weather + load note). */
export default function CheckpointPanel({ cp, loadLb, onClose }) {
  if (!cp) return null;
  return (
    <div className="cp-panel">
      <div className="cp-panel-head">
        <h3>Checkpoint — Mile {cp.mile}</h3>
        <button className="btn-x" onClick={onClose} aria-label="Close">
          ×
        </button>
      </div>
      <span
        className="risk-badge"
        style={{ background: COLORS[cp.risk_level] }}
      >
        {LEVELS[cp.risk_level]}
        {cp.no_travel ? " — Do not travel" : ""}
      </span>
      <dl className="cp-grid">
        <div>
          <dt>ETA</dt>
          <dd>{fmtEta(cp.eta)}</dd>
        </div>
        <div>
          <dt>Wind</dt>
          <dd>{cp.wind_mph} mph</dd>
        </div>
        <div>
          <dt>Rain</dt>
          <dd>{cp.rain_in_hr} in/hr</dd>
        </div>
        <div>
          <dt>Snow</dt>
          <dd>{cp.snow_in_hr} in/hr</dd>
        </div>
        <div>
          <dt>Temperature</dt>
          <dd>{cp.temp_c}°C</dd>
        </div>
        <div>
          <dt>Load</dt>
          <dd>{loadLb.toLocaleString()} lb</dd>
        </div>
      </dl>
      {cp.reasons.length > 0 && (
        <p className="cp-reasons">
          Why this risk: {cp.reasons.join(" · ")}
        </p>
      )}
      {cp.reasons.length === 0 && (
        <p className="cp-reasons ok">Conditions are within safe limits.</p>
      )}
    </div>
  );
}
