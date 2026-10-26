"""Weather risk classification and route ranking — pure functions.

Implements the Spotter assessment brief's risk tables exactly:

    Condition   Low        Moderate   High       Severe     No Travel
    Wind        <25 mph    25-34      35-44      45-54      >=55 mph
    Rain        <0.10      0.10-0.25  0.25-0.50  0.50-1.00  >1.00 in/hr
    Snow        <0.5       0.5-1.0    1.0-2.0    2.0-3.0    >3.0 in/hr

Boundary rule: the lower band is exclusive at its upper edge, so a value
sitting exactly on a boundary belongs to the higher band (e.g. 35 mph wind
is High, 45 mph is Severe, 55 mph is No Travel). This matches the brief's
ranges ("35-44 High", "45-54 Severe").

Load rules (applied after the base classification):
    * >=55 mph wind            -> No Travel, any load
    * 45-54 mph + >30,000 lb   -> No Travel
    * 35-44 mph + >40,000 lb   -> Severe

Route recommendation (brief order, with No Travel ranked before Severe
because a No Travel stretch is strictly worse than a Severe one):
    1. fewest No Travel miles
    2. fewest Severe miles
    3. fewest High miles
    4. lowest average risk
    5. shortest travel time

No Django imports here on purpose: this module is unit-testable in
isolation (see api/test_risk.py).
"""

LOW, MODERATE, HIGH, SEVERE, NO_TRAVEL = 0, 1, 2, 3, 4

LEVEL_NAMES = {
    LOW: "Low",
    MODERATE: "Moderate",
    HIGH: "High",
    SEVERE: "Severe",
    NO_TRAVEL: "No Travel",
}


def classify_wind(mph):
    """Wind speed (mph) -> risk level."""
    if mph >= 55:
        return NO_TRAVEL
    if mph >= 45:
        return SEVERE
    if mph >= 35:
        return HIGH
    if mph >= 25:
        return MODERATE
    return LOW


def classify_rain(in_per_hr):
    """Rainfall rate (inches/hour) -> risk level."""
    if in_per_hr > 1.00:
        return NO_TRAVEL
    if in_per_hr >= 0.50:
        return SEVERE
    if in_per_hr >= 0.25:
        return HIGH
    if in_per_hr >= 0.10:
        return MODERATE
    return LOW


def classify_snow(in_per_hr):
    """Snowfall rate (inches/hour) -> risk level."""
    if in_per_hr > 3.0:
        return NO_TRAVEL
    if in_per_hr >= 2.0:
        return SEVERE
    if in_per_hr >= 1.0:
        return HIGH
    if in_per_hr >= 0.5:
        return MODERATE
    return LOW


def checkpoint_risk(wind_mph, rain_in_hr, snow_in_hr, load_lb):
    """Full checkpoint risk: base tables + load rules.

    Returns (level, reasons) where reasons is a list of short human-readable
    strings explaining what drove the level (empty for Low).
    """
    level = max(
        classify_wind(wind_mph),
        classify_rain(rain_in_hr),
        classify_snow(snow_in_hr),
    )
    reasons = []
    if classify_wind(wind_mph) == level and wind_mph >= 25:
        reasons.append(f"Wind {wind_mph:.0f} mph")
    if classify_rain(rain_in_hr) == level and rain_in_hr >= 0.10:
        reasons.append(f"Rain {rain_in_hr:.2f} in/hr")
    if classify_snow(snow_in_hr) == level and snow_in_hr >= 0.5:
        reasons.append(f"Snow {snow_in_hr:.2f} in/hr")

    # Load rules (brief). Wind >= 55 mph is already No Travel from the table.
    if 45 <= wind_mph < 55 and load_lb > 30_000:
        level = NO_TRAVEL
        reasons.append(f"Wind {wind_mph:.0f} mph with {load_lb:,.0f} lb load")
    elif 35 <= wind_mph < 45 and load_lb > 40_000:
        level = max(level, SEVERE)
        reasons.append(f"Wind {wind_mph:.0f} mph with {load_lb:,.0f} lb load")

    return level, reasons


def rank_routes(summaries):
    """Return route indices ordered best-first per the brief's ranking.

    Each summary dict needs: no_travel_miles, severe_miles, high_miles,
    avg_risk, duration_min.
    """
    order = sorted(
        range(len(summaries)),
        key=lambda i: (
            summaries[i]["no_travel_miles"],
            summaries[i]["severe_miles"],
            summaries[i]["high_miles"],
            summaries[i]["avg_risk"],
            summaries[i]["duration_min"],
        ),
    )
    return order
