"""Shared frontend constants: nutrition goals, day-type multipliers, thresholds."""

BASE_GOALS = {"kcal": 2600, "protein_g": 180, "fat_g": 80, "carbs_g": 300, "fiber_g": 30, "water_ml": 2500}

# Per-day-type multipliers applied on top of BASE_GOALS.
GOAL_MULTIPLIERS = {
    "rest": {"kcal": 0.85},
    "refeed": {"kcal": 1.1, "carbs_g": 1.25},
}

STOCK_WARNING_THRESHOLD = 7


def goals_for(day_type: str) -> dict[str, float]:
    """Nutrition goals scaled by the day type (training/rest/refeed/custom)."""
    goals = dict(BASE_GOALS)
    for key, multiplier in GOAL_MULTIPLIERS.get(day_type, {}).items():
        goals[key] *= multiplier
    return goals
