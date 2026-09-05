from datetime import date, datetime

from fastapi import APIRouter, HTTPException

from app.models import BodyMetric, DoseLog, FoodEntry, Meal, ProtocolItem, Workout
from app.schemas import DayCloseIn
from app.services.common import default_user_id, dto
from app.services.days import get_or_create_day, refresh_completion
from app.services.nutrition import add_nutrients

router = APIRouter(prefix="/days", tags=["days"])


async def day_view(day_date: date) -> dict:
    user_id = await default_user_id()
    day = await refresh_completion(user_id, day_date)
    metric = await BodyMetric.find_one(BodyMetric.user_id == user_id, BodyMetric.date == day_date)
    workouts = await Workout.find(Workout.user_id == user_id, Workout.date == day_date).to_list()
    meals = await Meal.find(Meal.user_id == user_id, Meal.date == day_date).to_list()
    entries = []
    for meal in meals:
        entries.extend(await FoodEntry.find(FoodEntry.meal_id == meal.id).to_list())
    required = await ProtocolItem.find(ProtocolItem.user_id == user_id, ProtocolItem.archived == False).to_list()
    required = [i for i in required if i.is_required and i.start_date <= day_date and (not i.end_date or i.end_date >= day_date) and (not i.weekdays or day_date.isoweekday() in i.weekdays)]
    logs = await DoseLog.find(DoseLog.user_id == user_id, DoseLog.date == day_date).to_list()
    return {
        "day": dto(day), "metric": dto(metric) if metric else None,
        "workouts": [dto(item) for item in workouts],
        "meal_count": len(meals), "nutrition": add_nutrients([entry.nutrients for entry in entries]).model_dump(),
        "protocol": [{**dto(item), "taken": any(log.item_id == item.id and log.status == "taken" for log in logs)} for item in required],
        "uncompleted": {
            "protocol": [item.name for item in required if not any(log.item_id == item.id and log.status == "taken" for log in logs)],
            "workout": not any(item.completed or item.is_rest_day for item in workouts),
            "nutrition": not bool(entries), "metrics": metric is None,
        },
    }


@router.get("/today")
async def today() -> dict:
    return await day_view(date.today())


@router.post("/{day_date}/close")
async def close_day(day_date: date, payload: DayCloseIn) -> dict:
    user_id = await default_user_id()
    day = await refresh_completion(user_id, day_date)
    if day.closed:
        raise HTTPException(status_code=409, detail="Day is already closed")
    day.closed = True
    day.close_reason = payload.reason
    day.updated_at = datetime.utcnow()
    await day.save()
    return dto(day)


@router.get("/{day_date}")
async def details(day_date: date) -> dict:
    return await day_view(day_date)
