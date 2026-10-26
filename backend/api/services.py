"""External-service layer + plan assembly for Weather-Aware Truck Routing.

Free APIs only, no keys:
  * Nominatim (geocoding) — called from Django only, with a proper
    User-Agent header, per its usage policy.
  * OSRM demo server (routing) — `alternatives=3` plus via-point variants,
    because the demo server usually returns a single route even when asked
    for alternatives. Via points are placed perpendicular to the straight
    line between origin and destination; a candidate is kept only if it is
    genuinely different from routes already found and not an absurd detour.
  * Open-Meteo (weather) — batched multi-location requests, hourly
    wind_speed_10m / precipitation / snowfall / temperature_2m, UTC.

Weather math notes:
  * Units are converted once, here: km/h -> mph, mm -> in, cm -> in.
  * ETAs assume constant speed along the route (mile fraction x duration).
  * The 0-48h forecast slider reuses the same fetched hourly data: for each
    checkpoint we keep wind/rain/snow at departure+0h ... departure+48h, so
    the frontend can recolour the corridor instantly without new requests.
"""

import math
from datetime import datetime, timedelta, timezone

import requests

from .risk import LEVEL_NAMES, checkpoint_risk, rank_routes

UA = {"User-Agent": "spotter-weather-truck-routing/1.0 (assessment demo)"}
OSRM = "https://router.project-osrm.org/route/v1/driving"
NOMINATIM = "https://nominatim.openstreetmap.org/search"
OPEN_METEO = "https://api.open-meteo.com/v1/forecast"

KMH_TO_MPH = 0.621371
MM_TO_IN = 1 / 25.4
CM_TO_IN = 1 / 2.54

_geocode_cache = {}


# ---------------------------------------------------------------- helpers
def haversine_miles(lat1, lng1, lat2, lng2):
    """Great-circle distance in miles."""
    r = math.radians
    dlat = r(lat2 - lat1)
    dlng = r(lng2 - lng1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(r(lat1)) * math.cos(r(lat2)) * math.sin(dlng / 2) ** 2
    )
    return 3958.8 * 2 * math.asin(math.sqrt(a))


def _route_length_miles(coords):
    """Total length of an OSRM geometry ([lng, lat] pairs) in miles."""
    total = 0.0
    for (lng1, lat1), (lng2, lat2) in zip(coords, coords[1:]):
        total += haversine_miles(lat1, lng1, lat2, lng2)
    return total


# ---------------------------------------------------------------- geocode
def geocode(place):
    """Place name -> (lat, lng) or None. Results are cached in-memory."""
    key = place.strip().lower()
    if key in _geocode_cache:
        return _geocode_cache[key]
    r = requests.get(
        NOMINATIM,
        params={"q": place, "format": "json", "limit": 1},
        headers=UA,
        timeout=15,
    )
    r.raise_for_status()
    data = r.json()
    result = None
    if data:
        result = (float(data[0]["lat"]), float(data[0]["lon"]))
    _geocode_cache[key] = result
    return result


# ---------------------------------------------------------------- routing
def _osrm_route(coord_list):
    """One OSRM call for a list of (lat, lng) waypoints. Returns route or None."""
    path = ";".join(f"{lng},{lat}" for lat, lng in coord_list)
    r = requests.get(
        f"{OSRM}/{path}",
        params={"overview": "full", "geometries": "geojson"},
        timeout=25,
    )
    r.raise_for_status()
    routes = r.json().get("routes") or []
    if not routes:
        return None
    route = routes[0]
    return {
        "geometry": route["geometry"]["coordinates"],  # [[lng, lat], ...]
        "distance_miles": route["distance"] / 1609.34,
        "duration_min": route["duration"] / 60.0,
    }


def _sample_points(coords, count=24):
    """Evenly spaced (lat, lng) samples along a geometry."""
    total = _route_length_miles(coords)
    if total == 0 or count <= 1:
        return [(coords[0][1], coords[0][0])]
    step = total / (count - 1)
    samples = []
    acc = 0.0
    target = 0.0
    for (lng1, lat1), (lng2, lat2) in zip(coords, coords[1:]):
        seg = haversine_miles(lat1, lng1, lat2, lng2)
        while acc + seg >= target and len(samples) < count:
            frac = 0 if seg == 0 else (target - acc) / seg
            samples.append(
                (lat1 + frac * (lat2 - lat1), lng1 + frac * (lng2 - lng1))
            )
            target += step
        acc += seg
    if len(samples) < count:
        samples.append((coords[-1][1], coords[-1][0]))
    return samples[:count]


def _is_distinct(candidate_coords, existing_routes):
    """True if the candidate route differs from every existing route.

    A route counts as distinct when at least 30% of its sampled points lie
    more than 5 miles from the other route's geometry.
    """
    cand = _sample_points(candidate_coords, 24)
    for route in existing_routes:
        verts = route["geometry"][::5]  # subsample for speed
        far = 0
        for lat, lng in cand:
            nearest = min(
                haversine_miles(lat, lng, v[1], v[0]) for v in verts
            )
            if nearest > 5:
                far += 1
        if far / len(cand) < 0.30:
            return False
    return True


def build_routes(origin, destination):
    """Return up to 3 genuinely different routes between two (lat, lng) points.

    Strategy: direct OSRM route first (with alternatives=3 in case the demo
    server ever returns them), then via-point variants perpendicular to the
    straight line, at increasing offsets, until 3 distinct routes exist.
    """
    (lat1, lng1), (lat2, lng2) = origin, destination
    routes = []

    direct = _osrm_route([origin, destination])
    if direct is None:
        raise ValueError("No driving route found between these places.")
    routes.append(direct)

    # Perpendicular offsets (degrees) at the straight-line midpoint.
    mid_lat, mid_lng = (lat1 + lat2) / 2, (lng1 + lng2) / 2
    dlat, dlng = lat2 - lat1, lng2 - lng1
    norm = math.hypot(dlat, dlng) or 1.0
    perp_lat, perp_lng = -dlng / norm, dlat / norm

    for offset in (0.35, -0.35, 0.7, -0.7, 1.2, -1.2):
        if len(routes) >= 3:
            break
        via = (mid_lat + perp_lat * offset, mid_lng + perp_lng * offset)
        try:
            cand = _osrm_route([origin, via, destination])
        except Exception:
            continue
        if cand is None:
            continue
        # Reject absurd detours (more than 2x the direct drive time).
        if cand["duration_min"] > 2 * direct["duration_min"]:
            continue
        if _is_distinct(cand["geometry"], routes):
            routes.append(cand)

    return routes


# ---------------------------------------------------------------- sampling
def sample_checkpoints(coords, total_miles, interval_miles):
    """Points every `interval_miles` along the geometry, plus start and end.

    Returns [(mile, lat, lng), ...] with interpolated positions.
    """
    checkpoints = [(0.0, coords[0][1], coords[0][0])]
    target = float(interval_miles)
    acc = 0.0
    for (lng1, lat1), (lng2, lat2) in zip(coords, coords[1:]):
        seg = haversine_miles(lat1, lng1, lat2, lng2)
        while acc + seg >= target and target < total_miles:
            frac = 0 if seg == 0 else (target - acc) / seg
            checkpoints.append(
                (
                    round(target, 1),
                    lat1 + frac * (lat2 - lat1),
                    lng1 + frac * (lng2 - lng1),
                )
            )
            target += interval_miles
        acc += seg
    if checkpoints[-1][0] < total_miles:
        checkpoints.append(
            (round(total_miles, 1), coords[-1][1], coords[-1][0])
        )
    return checkpoints


# ---------------------------------------------------------------- weather
def _parse_hourly_times(times):
    return [
        datetime.strptime(t, "%Y-%m-%dT%H:%M").replace(tzinfo=timezone.utc)
        for t in times
    ]


def _nearest_index(times, target):
    """Index of the hourly timestamp closest to target."""
    best_i, best_diff = 0, None
    for i, t in enumerate(times):
        diff = abs((t - target).total_seconds())
        if best_diff is None or diff < best_diff:
            best_i, best_diff = i, diff
    return best_i


def fetch_weather(points, start_date, end_date):
    """Batched Open-Meteo hourly forecast for many (lat, lng) points.

    Returns a list aligned with `points`, each item:
    {"times": [datetime...], "wind_mph": [...], "rain_in_hr": [...],
     "snow_in_hr": [...], "temp_c": [...]}.
    Requests are chunked (60 locations each) to stay within URL limits.
    """
    results = []
    for i in range(0, len(points), 60):
        chunk = points[i : i + 60]
        lat_s = ",".join(f"{lat:.5f}" for lat, _ in chunk)
        lng_s = ",".join(f"{lng:.5f}" for _, lng in chunk)
        r = requests.get(
            OPEN_METEO,
            params={
                "latitude": lat_s,
                "longitude": lng_s,
                "hourly": "wind_speed_10m,precipitation,snowfall,temperature_2m",
                "timezone": "UTC",
                "start_date": start_date,
                "end_date": end_date,
            },
            timeout=30,
        )
        r.raise_for_status()
        data = r.json()
        if not isinstance(data, list):
            data = [data]
        for loc in data:
            h = loc["hourly"]
            results.append(
                {
                    "times": _parse_hourly_times(h["time"]),
                    "wind_mph": [v * KMH_TO_MPH for v in h["wind_speed_10m"]],
                    "rain_in_hr": [v * MM_TO_IN for v in h["precipitation"]],
                    "snow_in_hr": [v * CM_TO_IN for v in h["snowfall"]],
                    "temp_c": h["temperature_2m"],
                }
            )
    return results


def summarize_route(checkpoints, total_miles):
    """Mile-weighted risk summary for one route's checkpoints.

    Each checkpoint 'owns' the stretch until the next checkpoint (the last
    one owns the remainder). Pure function — unit-tested in test_risk.py
    via test_summarize_route.
    """
    miles_by_level = {0: 0.0, 1: 0.0, 2: 0.0, 3: 0.0, 4: 0.0}
    weighted = 0.0
    for k, cp in enumerate(checkpoints):
        nxt = (
            checkpoints[k + 1]["mile"]
            if k + 1 < len(checkpoints)
            else total_miles
        )
        stretch = max(0.0, nxt - cp["mile"])
        miles_by_level[cp["risk_level"]] += stretch
        weighted += stretch * cp["risk_level"]
    avg_risk = weighted / total_miles if total_miles else 0.0
    worst = max(checkpoints, key=lambda c: c["risk_level"])
    return {
        "low_miles": round(miles_by_level[0], 1),
        "moderate_miles": round(miles_by_level[1], 1),
        "high_miles": round(miles_by_level[2], 1),
        "severe_miles": round(miles_by_level[3], 1),
        "no_travel_miles": round(miles_by_level[4], 1),
        "avg_risk": round(avg_risk, 2),
        "worst_checkpoint": {
            "mile": worst["mile"],
            "risk": worst["risk"],
            "reasons": worst["reasons"],
        },
    }


# ---------------------------------------------------------------- plan
def build_plan(origin_name, destination_name, departure, load_lb, interval_miles):
    """Full assessment plan: routes + ETA weather + risk + recommendation."""
    origin = geocode(origin_name)
    destination = geocode(destination_name)
    if origin is None:
        raise ValueError(f"Could not find a place called '{origin_name}'.")
    if destination is None:
        raise ValueError(f"Could not find a place called '{destination_name}'.")

    routes = build_routes(origin, destination)

    # Forecast window: departure day through departure+4 days (covers the
    # 0-48h slider and ETAs on long trips).
    start_date = departure.strftime("%Y-%m-%d")
    end_date = (departure + timedelta(days=4)).strftime("%Y-%m-%d")

    # Sample checkpoints for every route, then fetch all weather in batches.
    per_route_points = []
    all_points = []
    for route in routes:
        pts = sample_checkpoints(
            route["geometry"], route["distance_miles"], interval_miles
        )
        per_route_points.append(pts)
        all_points.extend((lat, lng) for _, lat, lng in pts)
    weather = fetch_weather(all_points, start_date, end_date)

    out_routes = []
    w_i = 0
    for r_i, route in enumerate(routes):
        pts = per_route_points[r_i]
        total_miles = route["distance_miles"]
        duration_min = route["duration_min"]
        checkpoints = []
        for mile, lat, lng in pts:
            w = weather[w_i]
            w_i += 1
            eta = departure + timedelta(
                minutes=duration_min * (mile / total_miles if total_miles else 0)
            )
            h = _nearest_index(w["times"], eta)
            wind = w["wind_mph"][h]
            rain = w["rain_in_hr"][h]
            snow = w["snow_in_hr"][h]
            level, reasons = checkpoint_risk(wind, rain, snow, load_lb)
            # 0-48h slider series (hourly, from departure).
            slider = {"wind_mph": [], "rain_in_hr": [], "snow_in_hr": []}
            for off in range(0, 49):
                j = _nearest_index(w["times"], departure + timedelta(hours=off))
                slider["wind_mph"].append(round(w["wind_mph"][j], 1))
                slider["rain_in_hr"].append(round(w["rain_in_hr"][j], 3))
                slider["snow_in_hr"].append(round(w["snow_in_hr"][j], 3))
            checkpoints.append(
                {
                    "mile": mile,
                    "lat": round(lat, 5),
                    "lng": round(lng, 5),
                    "eta": eta.isoformat(),
                    "wind_mph": round(wind, 1),
                    "rain_in_hr": round(rain, 3),
                    "snow_in_hr": round(snow, 3),
                    "temp_c": round(w["temp_c"][h], 1),
                    "risk_level": level,
                    "risk": LEVEL_NAMES[level],
                    "no_travel": level == 4,
                    "reasons": reasons,
                    "forecast": slider,
                }
            )

        # Mile-weighted summary (see summarize_route).
        summary = summarize_route(checkpoints, total_miles)
        out_routes.append(
            {
                "id": r_i,
                "name": f"Route {r_i + 1}",
                "distance_miles": round(total_miles, 1),
                "duration_min": round(duration_min),
                "geometry": [[lat, lng] for lng, lat in route["geometry"]],
                "checkpoints": checkpoints,
                "summary": summary,
            }
        )

    summaries = [
        {
            "no_travel_miles": r["summary"]["no_travel_miles"],
            "severe_miles": r["summary"]["severe_miles"],
            "high_miles": r["summary"]["high_miles"],
            "avg_risk": r["summary"]["avg_risk"],
            "duration_min": r["duration_min"],
        }
        for r in out_routes
    ]
    order = rank_routes(summaries)
    best = order[0]
    for r_i, r in enumerate(out_routes):
        r["recommended"] = r_i == best
    best_summary = out_routes[best]["summary"]
    reason_bits = []
    if best_summary["no_travel_miles"] == 0 and best_summary["severe_miles"] == 0:
        reason_bits.append("no Severe or No Travel stretches")
    else:
        reason_bits.append(
            f"fewest risky miles ({best_summary['severe_miles']} Severe, "
            f"{best_summary['no_travel_miles']} No Travel)"
        )
    reason_bits.append(f"lowest average risk ({best_summary['avg_risk']})")

    return {
        "origin": {"name": origin_name, "lat": origin[0], "lng": origin[1]},
        "destination": {
            "name": destination_name,
            "lat": destination[0],
            "lng": destination[1],
        },
        "departure": departure.isoformat(),
        "load_weight_lb": load_lb,
        "sample_interval_miles": interval_miles,
        "routes": out_routes,
        "recommendation": {
            "route_id": best,
            "route_name": out_routes[best]["name"],
            "reason": "Recommended route: " + "; ".join(reason_bits) + ".",
        },
    }
