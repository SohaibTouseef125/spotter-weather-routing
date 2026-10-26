"""API views — Weather-Aware Truck Routing.

POST /api/plan/  — the assessment endpoint. Body (JSON):
    {
      "origin": "Karachi", "destination": "Lahore",
      "departure": "2026-10-24T08:00:00+00:00",   # ISO 8601; naive = UTC
      "load_weight_lb": 35000,
      "sample_interval_miles": 25              # 10, 25 or 50
    }
Returns routes with ETA weather checkpoints, risk levels, summaries and
the recommended route (see api/services.py).

GET /api/health/ — liveness check for deploys and the frontend.
"""

import json
from datetime import datetime, timedelta, timezone

from rest_framework.decorators import api_view
from rest_framework.response import Response

from .services import build_plan


@api_view(["GET"])
def health(request):
    return Response({"status": "ok"})


@api_view(["POST"])
def plan(request):
    try:
        body = json.loads(request.body or b"{}")
    except json.JSONDecodeError:
        return Response({"error": "Request body must be valid JSON."}, status=400)

    origin = (body.get("origin") or "").strip()
    destination = (body.get("destination") or "").strip()
    if not origin or not destination:
        return Response(
            {"error": "Both 'origin' and 'destination' are required."}, status=400
        )

    try:
        load_lb = float(body.get("load_weight_lb", 0) or 0)
    except (TypeError, ValueError):
        return Response({"error": "'load_weight_lb' must be a number."}, status=400)
    if not 0 <= load_lb <= 100_000:
        return Response(
            {"error": "'load_weight_lb' must be between 0 and 100,000."}, status=400
        )

    interval = body.get("sample_interval_miles", 25)
    if interval not in (10, 25, 50):
        return Response(
            {"error": "'sample_interval_miles' must be 10, 25 or 50."}, status=400
        )

    departure_raw = body.get("departure") or ""
    try:
        departure = datetime.fromisoformat(departure_raw.replace("Z", "+00:00"))
    except ValueError:
        return Response(
            {"error": "'departure' must be an ISO 8601 date/time."}, status=400
        )
    if departure.tzinfo is None:
        departure = departure.replace(tzinfo=timezone.utc)
    now = datetime.now(timezone.utc)
    if departure < now - timedelta(days=1) or departure > now + timedelta(days=16):
        return Response(
            {
                "error": "Departure must be within the last day and the next "
                "16 days (Open-Meteo forecast range)."
            },
            status=400,
        )

    try:
        result = build_plan(origin, destination, departure, load_lb, interval)
    except ValueError as e:
        return Response({"error": str(e)}, status=400)
    except Exception as e:  # upstream API failure etc.
        return Response({"error": f"Could not build a plan: {e}"}, status=502)
    return Response(result)
