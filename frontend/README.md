# Frontend — Weather-Aware Truck Routing (React + Vite + Leaflet)

Professional UI for the Spotter assessment: plan up to 3 routes, inspect
weather risk at every checkpoint, and scrub a 0–48h forecast slider.

## Run locally

```bash
cd frontend
npm install
npm run dev        # http://localhost:5173 (expects Django on :8000)
```

Point at a deployed backend with a `.env` file:

```
VITE_API_URL=https://your-render-backend.onrender.com
```

## What it shows

- **Form** — origin, destination, departure date/time, load weight (lb),
  weather sample interval (10 / 25 / 50 miles).
- **Route cards** — distance, drive time, average risk, a colour-coded
  risk breakdown bar, Severe / No Travel miles, and the recommended route
  (★ badge + reason).
- **Map** — all routes as polylines (selected route highlighted),
  origin/destination markers, and checkpoint dots coloured by risk.
  Clicking a checkpoint opens its detail panel (ETA, wind, rain, snow,
  temperature, load note, why-this-risk).
- **Corridor risk heatmap** — a clickable mile-by-mile risk strip for the
  selected route.
- **Forecast slider** — ETA weather mode (checkpoints coloured by weather
  at the truck's estimated arrival time) or forecast mode (0–48h slider
  from departure; colours recompute instantly in the browser from the
  forecast series the backend already returned — no extra requests).
- **Risk legend** — the brief's wind / rain / snow tables and load rules.

## Structure

- `src/App.jsx` — layout + form + view-mode state
- `src/api.js` — backend client (`VITE_API_URL`)
- `src/risk.js` — risk classification mirroring `backend/api/risk.py`
- `src/components/MapView.jsx` — Leaflet map, routes, checkpoints
- `src/components/RouteCards.jsx` — route cards + heat strip
- `src/components/CheckpointPanel.jsx` — checkpoint detail

## Deploy (Vercel, free)

vercel.com → Add New Project → GitHub repo → Root Directory: `frontend`
→ Environment Variable `VITE_API_URL=<your Render backend URL>` →
Deploy. `vercel.json` in this folder pins the Vite build settings.
