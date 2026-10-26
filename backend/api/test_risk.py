"""Unit tests for the brief's risk tables, load rules and ranking.

Run from backend/:  .venv/bin/python -m pytest api/test_risk.py -v
No Django setup needed — api/risk.py is dependency-free.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.risk import (
    HIGH,
    LOW,
    MODERATE,
    NO_TRAVEL,
    SEVERE,
    checkpoint_risk,
    classify_rain,
    classify_snow,
    classify_wind,
    rank_routes,
)


def test_wind_thresholds():
    assert classify_wind(0) == LOW
    assert classify_wind(24.9) == LOW
    assert classify_wind(25) == MODERATE
    assert classify_wind(34.9) == MODERATE
    assert classify_wind(35) == HIGH
    assert classify_wind(44.9) == HIGH
    assert classify_wind(45) == SEVERE
    assert classify_wind(54.9) == SEVERE
    assert classify_wind(55) == NO_TRAVEL
    assert classify_wind(80) == NO_TRAVEL


def test_rain_thresholds():
    assert classify_rain(0) == LOW
    assert classify_rain(0.09) == LOW
    assert classify_rain(0.10) == MODERATE
    assert classify_rain(0.24) == MODERATE
    assert classify_rain(0.25) == HIGH
    assert classify_rain(0.49) == HIGH
    assert classify_rain(0.50) == SEVERE
    assert classify_rain(1.00) == SEVERE
    assert classify_rain(1.01) == NO_TRAVEL


def test_snow_thresholds():
    assert classify_snow(0) == LOW
    assert classify_snow(0.49) == LOW
    assert classify_snow(0.5) == MODERATE
    assert classify_snow(0.99) == MODERATE
    assert classify_snow(1.0) == HIGH
    assert classify_snow(1.99) == HIGH
    assert classify_snow(2.0) == SEVERE
    assert classify_snow(3.0) == SEVERE
    assert classify_snow(3.01) == NO_TRAVEL


def test_load_rule_no_travel_any_load():
    # >=55 mph wind is No Travel regardless of load.
    assert checkpoint_risk(60, 0, 0, 0)[0] == NO_TRAVEL
    assert checkpoint_risk(60, 0, 0, 80_000)[0] == NO_TRAVEL


def test_load_rule_heavy_load_severe_wind():
    # 45-54 mph + >30,000 lb -> No Travel; at/below 30,000 stays Severe.
    assert checkpoint_risk(50, 0, 0, 30_001)[0] == NO_TRAVEL
    assert checkpoint_risk(50, 0, 0, 30_000)[0] == SEVERE
    assert checkpoint_risk(50, 0, 0, 0)[0] == SEVERE


def test_load_rule_heavy_load_high_wind():
    # 35-44 mph + >40,000 lb -> Severe; at/below 40,000 stays High.
    assert checkpoint_risk(40, 0, 0, 40_001)[0] == SEVERE
    assert checkpoint_risk(40, 0, 0, 40_000)[0] == HIGH
    # A lighter load does not upgrade a Low wind checkpoint.
    assert checkpoint_risk(20, 0, 0, 45_000)[0] == LOW


def test_worst_condition_wins():
    # Base level is the max across wind/rain/snow.
    assert checkpoint_risk(10, 0.6, 0, 0)[0] == SEVERE  # rain dominates
    assert checkpoint_risk(10, 0, 2.5, 0)[0] == SEVERE  # snow dominates
    assert checkpoint_risk(30, 0.05, 0, 0)[0] == MODERATE


def _summary(no_travel=0, severe=0, high=0, avg=0, dur=100):
    return {
        "no_travel_miles": no_travel,
        "severe_miles": severe,
        "high_miles": high,
        "avg_risk": avg,
        "duration_min": dur,
    }


def test_ranking_order():
    # Brief order: fewest Severe miles, then fewest High miles, then
    # lowest average risk, then shortest time (No Travel ranks first).
    routes = [
        _summary(severe=10, high=0, avg=1.0, dur=100),   # worst: most severe
        _summary(severe=2, high=20, avg=1.0, dur=100),   # more high miles
        _summary(severe=2, high=5, avg=1.5, dur=100),    # higher avg risk
        _summary(severe=2, high=5, avg=1.0, dur=200),    # slower
        _summary(severe=2, high=5, avg=1.0, dur=100),    # best
    ]
    assert rank_routes(routes) == [4, 3, 2, 1, 0]


def test_ranking_no_travel_first():
    routes = [
        _summary(severe=0, high=0, avg=0, dur=50),
        _summary(no_travel=5, severe=0, high=0, avg=0, dur=50),
    ]
    assert rank_routes(routes) == [0, 1]


def test_ranking_tie_break_by_time():
    routes = [_summary(dur=300), _summary(dur=120), _summary(dur=200)]
    assert rank_routes(routes) == [1, 2, 0]


def test_summarize_route():
    from api.services import summarize_route

    cps = [
        {"mile": 0, "risk_level": 0, "risk": "Low", "reasons": []},
        {"mile": 25, "risk_level": 2, "risk": "High", "reasons": ["Wind 40 mph"]},
        {"mile": 50, "risk_level": 4, "risk": "No Travel", "reasons": ["Wind 60 mph"]},
    ]
    s = summarize_route(cps, 100)
    # Checkpoint at mile 0 owns 0-25, mile 25 owns 25-50, mile 50 owns 50-100.
    assert s["low_miles"] == 25
    assert s["high_miles"] == 25
    assert s["no_travel_miles"] == 50
    assert s["severe_miles"] == 0
    assert s["avg_risk"] == 2.5  # (25*0 + 25*2 + 50*4) / 100
    assert s["worst_checkpoint"]["mile"] == 50
    assert s["worst_checkpoint"]["risk"] == "No Travel"
