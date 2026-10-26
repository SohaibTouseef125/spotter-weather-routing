/* Risk logic — mirrors backend/api/risk.py exactly (same thresholds).
 * Used for the 0-48h forecast slider so checkpoint colours update instantly
 * without new API calls. Levels: 0 Low, 1 Moderate, 2 High, 3 Severe,
 * 4 No Travel.
 */

export const LEVELS = ["Low", "Moderate", "High", "Severe", "No Travel"];

export const COLORS = {
  0: "#22c55e",
  1: "#eab308",
  2: "#f97316",
  3: "#ef4444",
  4: "#7f1d1d",
};

export function classifyWind(mph) {
  if (mph >= 55) return 4;
  if (mph >= 45) return 3;
  if (mph >= 35) return 2;
  if (mph >= 25) return 1;
  return 0;
}

export function classifyRain(inPerHr) {
  if (inPerHr > 1.0) return 4;
  if (inPerHr >= 0.5) return 3;
  if (inPerHr >= 0.25) return 2;
  if (inPerHr >= 0.1) return 1;
  return 0;
}

export function classifySnow(inPerHr) {
  if (inPerHr > 3.0) return 4;
  if (inPerHr >= 2.0) return 3;
  if (inPerHr >= 1.0) return 2;
  if (inPerHr >= 0.5) return 1;
  return 0;
}

/** Full checkpoint risk incl. load rules. Returns { level, reasons }. */
export function checkpointRisk(windMph, rainInHr, snowInHr, loadLb) {
  let level = Math.max(
    classifyWind(windMph),
    classifyRain(rainInHr),
    classifySnow(snowInHr)
  );
  const reasons = [];
  if (classifyWind(windMph) === level && windMph >= 25)
    reasons.push(`Wind ${windMph.toFixed(0)} mph`);
  if (classifyRain(rainInHr) === level && rainInHr >= 0.1)
    reasons.push(`Rain ${rainInHr.toFixed(2)} in/hr`);
  if (classifySnow(snowInHr) === level && snowInHr >= 0.5)
    reasons.push(`Snow ${snowInHr.toFixed(2)} in/hr`);
  if (windMph >= 45 && windMph < 55 && loadLb > 30000) {
    level = 4;
    reasons.push(`Wind ${windMph.toFixed(0)} mph with ${loadLb.toLocaleString()} lb load`);
  } else if (windMph >= 35 && windMph < 45 && loadLb > 40000) {
    level = Math.max(level, 3);
    reasons.push(`Wind ${windMph.toFixed(0)} mph with ${loadLb.toLocaleString()} lb load`);
  }
  return { level, reasons };
}

export function fmtDuration(min) {
  const h = Math.floor(min / 60);
  const m = Math.round(min % 60);
  return h > 0 ? `${h}h ${m}m` : `${m}m`;
}

export function fmtEta(iso) {
  return new Date(iso).toLocaleString([], {
    weekday: "short",
    hour: "numeric",
    minute: "2-digit",
  });
}
