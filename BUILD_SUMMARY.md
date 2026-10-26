# BUILD SUMMARY — Spotter Assessment: Weather-Aware Truck Routing

Built 2026-10-24 from the real brief
(`spotter_assessment_2026-10-23.pdf`). The earlier scaffold/ folder has
been promoted into the clean top-level layout below; the old
`spotter-assessment.zip` is superseded and can be ignored.

## Final directory

`/home/hatch/workspace/spotter-assessment/`

```
README.md            overview + run + deploy instructions
BUILD_SUMMARY.md     this file
render.yaml          Render blueprint (backend, one-click)
backend/             Django API (weather_route project + api app)
  api/risk.py        pure risk tables, load rules, ranking (unit-tested)
  api/services.py    Nominatim / OSRM / Open-Meteo + plan assembly
  api/views.py       POST /api/plan/ + GET /api/health/
  api/test_risk.py   pytest suite (11 tests)
  requirements.txt   django, drf, cors-headers, requests, gunicorn
  Procfile           gunicorn start command for Render
frontend/            React + Vite + Leaflet UI
  src/App.jsx        layout, form, ETA/forecast view modes
  src/api.js         backend client (VITE_API_URL)
  src/risk.js        risk logic mirroring backend (for instant slider)
  src/components/    MapView, RouteCards (+HeatStrip), CheckpointPanel
  vercel.json        Vite build settings for Vercel
```

## What was built (against the brief)

- **Inputs:** origin, destination, departure date/time, load weight (lb),
  sample interval 10 / 25 / 50 miles.
- **3 route options:** OSRM routing; because OSRM's demo server usually
  returns a single route, alternatives are built with perpendicular
  via-points and kept only if genuinely different (≥30% of sampled points
  >5 miles from existing routes) and not an absurd detour (≤2× direct
  time). US pairs with real highway alternatives return 3; pairs with a
  single fast corridor (e.g. Karachi → Lahore) return 2 — documented in
  backend/README.md.
- **Weather sampling:** Open-Meteo batched hourly forecast (wind km/h→mph,
  precipitation mm→in/hr, snowfall cm→in/hr), one batched call per 60
  checkpoints, at each checkpoint's ETA (departure + mile-fraction ×
  duration).
- **Risk:** exact brief tables (wind <25 / 25–34 / 35–44 / 45–54 / ≥55 mph;
  rain <0.10 / 0.10–0.25 / 0.25–0.50 / 0.50–1.00 / >1.00 in/hr; snow <0.5 /
  0.5–1.0 / 1.0–2.0 / 2.0–3.0 / >3.0 in/hr) + load rules (≥55 mph = No
  Travel any load; 45–54 mph + >30,000 lb = No Travel; 35–44 mph +
  >40,000 lb = Severe).
- **Recommendation:** fewest No Travel miles, then fewest Severe miles,
  then fewest High miles, then lowest average risk (mile-weighted), then
  shortest time. (No Travel ranks before Severe because it is strictly
  worse; with no No Travel miles the order is exactly the brief's.)
- **Map + UI:** all routes, checkpoints with risk colours + ETAs, route
  summary cards, corridor risk heat strip, legend, responsive layout.
- **Heatmap + 0–48h slider:** each checkpoint carries a 49-hour forecast
  series from departure, so the slider recolours the corridor instantly
  with no new requests; ETA-weather mode is the default view.
- **Free APIs only, no keys:** OSRM, Open-Meteo, Nominatim (called from
  Django only, with a proper User-Agent).

## Verification (all done 2026-10-24, local)

- **pytest: 11/11 passed** — wind / rain / snow thresholds, all three load
  rules, ranking order (incl. No Travel first and time tie-break),
  mile-weighted summary math.
  Run: `cd backend && .venv/bin/python -m pytest api/test_risk.py -v`
- **curl, Karachi → Lahore, 25 mi, 35,000 lb:** 2 routes
  (753.6 mi / 829 min recommended; 862.1 mi / 1,645 min alternative),
  32 + 36 checkpoints, real wind/rain/snow values at ETAs, 49-point
  forecast series per checkpoint, summary miles summing to route distance.
- **curl, Dallas → Houston, 50 mi, 45,000 lb:** 3 routes
  (238.5 mi / 253 min recommended; 280.0 mi / 322 min; 277.5 mi / 330 min).
- **Frontend:** `npm run build` clean (74 modules, 3.28 s, dist/ produced).
- **Note:** both verified city pairs had clear weather, so live checkpoints
  were all Low; non-Low risk paths are covered by the unit tests above,
  not by a live storm sample.

## Deploy (one-click, once the user is ready)

1. **Backend → Render:** New → Blueprint → this repo (`render.yaml`),
   or manual Web Service (root `backend/`, build
   `pip install -r requirements.txt`, start
   `gunicorn weather_route.wsgi:application --bind 0.0.0.0:$PORT`).
   Health check: `<render-url>/api/health/` → `{"status": "ok"}`.
2. **Frontend → Vercel:** import repo, Root Directory `frontend`,
   env `VITE_API_URL=<render backend URL>`, Deploy.
3. Open the live app once (Render free tier sleeps; first load is slow).

## Still needed from the user (NOT done — no accounts connected)

1. **Create a GitHub repo** and push this folder (no repo exists yet;
   no URL invented here).
2. **Deploy logins:** run the Render + Vercel steps above (or hand the
   browser over for them).
3. **Loom walkthrough (5–10 min):** form → routes → checkpoint click →
   forecast slider → code tour. Then email Ena the GitHub + live-app +
   Loom links (template was in the earlier BUILD_PLAN.md).
4. **Deadline:** assessment brief arrived 2026-10-23 evening; 4-day window
   ends ~2026-10-27 evening PKT. Do not let deployment slip past that.
