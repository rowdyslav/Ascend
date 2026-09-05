from app.models.nutrition import Nutrients


def scale_nutrients(per_100g: Nutrients, weight_g: float) -> Nutrients:
    """Scale every nutrient, including optional micronutrients, to a portion."""
    multiplier = weight_g / 100.0
    values = per_100g.model_dump()
    return Nutrients(**{key: (value * multiplier if value is not None else None) for key, value in values.items()})


def add_nutrients(items: list[Nutrients]) -> Nutrients:
    totals: dict[str, float | None] = {}
    always_present = {"kcal", "protein_g", "fat_g", "carbs_g", "water_ml"}
    for field in Nutrients.model_fields:
        values = [getattr(item, field) for item in items if getattr(item, field) is not None]
        totals[field] = sum(values) if values else (0.0 if field in always_present else None)
    return Nutrients(**totals)
