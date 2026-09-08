from datetime import date, datetime

from app.core.config import get_settings
from app.models import BodyMetric, Day, DoseLog, FoodEntry, Meal, ProtocolItem, Workout
from app.services.protocol import item_is_due


async def get_or_create_day(user_id, day_date: date) -> Day:
    day = await Day.find_one(Day.user_id == user_id, Day.date == day_date)
    if day is None:
        day = Day(user_id=user_id, date=day_date)
        await day.insert()
    return day


async def refresh_completion(user_id, day_date: date) -> Day:
    day = await get_or_create_day(user_id, day_date)
    weights = get_settings().completion_weights
    active_items = await ProtocolItem.find(
        ProtocolItem.user_id == user_id, ProtocolItem.archived == False,
        ProtocolItem.start_date <= day_date,
    ).to_list()
    active_items = [item for item in active_items if item.is_required and item_is_due(item, day_date)]
    logs = await DoseLog.find(DoseLog.user_id == user_id, DoseLog.date == day_date, DoseLog.status == "taken").to_list()
    protocol = (len({log.item_id for log in logs}) / len(active_items)) if active_items else 1.0
    workouts = await Workout.find(Workout.user_id == user_id, Workout.date == day_date).to_list()
    workout = 1.0 if any(item.completed or item.is_rest_day for item in workouts) else 0.0
    meals = await Meal.find(Meal.user_id == user_id, Meal.date == day_date).to_list()
    meal_ids = [meal.id for meal in meals]
    entry_count = await FoodEntry.find({"meal_id": {"$in": meal_ids}}).count() if meal_ids else 0
    nutrition = 1.0 if entry_count else 0.0
    # Daily checks are represented by a body metric entry in this MVP.
    checks = 1.0 if await BodyMetric.find_one(BodyMetric.user_id == user_id, BodyMetric.date == day_date) else 0.0
    day.completion_pct = round(100 * (weights["protocol"] * protocol + weights["workout"] * workout + weights["nutrition"] * nutrition + weights["checks"] * checks), 1)
    day.updated_at = datetime.utcnow()
    await day.save()
    return day
