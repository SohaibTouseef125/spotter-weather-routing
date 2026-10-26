# Weather-Aware Truck Routing — Spotter Full Stack Developer Assessment

A React + Django web app that helps a truck driver choose the safest
route based on weather, load weight, and travel time.

Enter origin, destination, departure date/time and load weight. The app
generates up to 3 route options (OSRM), samples weather every 10 / 25 /
50 miles along each route at the truck's estimated arrival time
(Open-Meteo), classifies risk with the brief's wind / rain / snow tables
plus load rules, recommends the best route, and shows everything on a
map — with a weather heatmap along the trip corridor and a 0–48 hour
forecast slider.

## Layout (one repo, two apps)

```
backend/    Django API (see backend/README.md)
frontend/   React + Vite + Leaflet UI (see frontend/README.md)
render.yaml Render blueprint for the backend (one-click deploy)
BUILD_SUMMARY.md  What was built, verification, remaining steps
```

## Run locally

```bash
# Backend (terminal 1)
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python manage.py runserver        # http://127.0.0.1:8000

# Frontend (terminal 2)
cd frontend
npm install
npm run dev                        # http://localhost:5173
```

No API keys needed anywhere: OSRM routing, Open-Meteo weather and
Nominatim geocoding are all free and keyless.

## Deploy

- **Backend → Render (free):** use the root `render.yaml` blueprint, or
  create a Web Service manually (root `backend/`, build
  `pip install -r requirements.txt`, start
  `gunicorn weather_route.wsgi:application --bind 0.0.0.0:$PORT`).
- **Frontend → Vercel (free):** import the repo with Root Directory
  `frontend` and set `VITE_API_URL` to the Render backend URL.
- Then record the 5–10 min Loom walkthrough and send Ena the GitHub +
  live-app + Loom links (see BUILD_SUMMARY.md).

## Evaluation mapping (per the brief)

- **40% routes / weather / risk / recommendation** — OSRM routes with
  via-point alternatives, ETA-based weather sampling, exact brief
  thresholds + load rules, brief-order recommendation ranking.
- **40% UI / map / heatmap smoothness** — polished layout, route cards,
  colour-coded checkpoints, corridor heat strip, instant 0–48h slider
  (no refetch).
- **15% code quality** — separated risk logic (pure, unit-tested),
  services layer, documented API contract.
- **5% documentation & walkthrough** — this README, per-app READMEs,
  BUILD_SUMMARY.md; Loom still to record (user's step).
