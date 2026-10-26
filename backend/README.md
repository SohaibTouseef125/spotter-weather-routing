# Backend — Weather-Aware Truck Routing (Django API)

API-only Django project: no templates, no database tables (in-memory only).
It serves one endpoint that the React frontend calls.

## Run locally

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python manage.py runserver        # http://127.0.0.1:8000
```

## Endpoints

- `GET /api/health/` → `{"status": "ok"}`
- `POST /api/plan/` — body:

```json
{
  "origin": "Dallas",
  "destination": "Houston",
  "departure": "2026-10-24T14:00:00Z",
  "load_weight_lb": 35000,
  "sample_interval_miles": 25
}
```

Response: `origin`, `destination`, `departure`, `load_weight_lb`,
`sample_interval_miles`, `routes[]` (each with `geometry` as `[lat, lng]`
pairs, `distance_miles`, `duration_min`, `recommended`, `checkpoints[]`
with mile / ETA / wind / rain / snow / temp / risk, plus a 0–48h
`forecast` series per checkpoint), `summary` (mile-weighted Low /
Moderate / High / Severe / No Travel miles + average risk), and
`recommendation` (best route + reason).

Validation: departure must be within the last day and the next 16 days
(Open-Meteo forecast range); interval must be 10, 25 or 50;
load weight 0–100,000 lb.

## How it works (`api/`)

- `services.py` — Nominatim geocoding (Django-side only, with User-Agent),
  OSRM routing, Open-Meteo batched weather, checkpoint sampling, plan
  assembly. OSRM's demo server usually returns a single route, so
  alternatives are built with perpendicular via-points and kept only if
  genuinely different (≥30% of sampled points >5 miles from existing
  routes) and not an absurd detour (≤2× direct drive time). Pairs with a
  single fast corridor (e.g. Karachi → Lahore) may therefore return 2
  routes instead of 3 — that is a data limit, not a bug.
- `risk.py` — pure risk tables, load rules and route ranking (no Django
  imports, so it is unit-testable on its own).
- `views.py` — request validation + error mapping.

## Tests

```bash
cd backend
.venv/bin/python -m pytest api/test_risk.py -v
```

Covers wind / rain / snow thresholds, all three load rules, the
recommendation ranking order, and mile-weighted route summaries.

## Deploy (Render, free)

Root `render.yaml` is a one-click blueprint (web service, `backend/`
root, gunicorn start command, `/api/health/` health check). Or manually:
New Web Service → repo, root directory `backend`, build
`pip install -r requirements.txt`, start
`gunicorn weather_route.wsgi:application --bind 0.0.0.0:$PORT`,
env `DJANGO_DEBUG=False`, `DJANGO_ALLOWED_HOSTS=*`,
`DJANGO_SECRET_KEY` (generate). CORS allows all origins, so the Vercel
frontend works without extra config.
