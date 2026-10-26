/* Backend API client. Base URL comes from VITE_API_URL at build time
 * (Vercel env var) and falls back to the local Django dev server. */

const API = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

export async function fetchPlan({ origin, destination, departure, loadLb, interval }) {
  const res = await fetch(`${API}/api/plan/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      origin,
      destination,
      departure,
      load_weight_lb: loadLb,
      sample_interval_miles: interval,
    }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || `Backend error (${res.status})`);
  return data;
}
