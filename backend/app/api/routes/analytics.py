from collections import defaultdict
from datetime import date, timedelta

from fastapi import APIRouter, Query

from app.core.config import get_settings
from app.models import BodyMetric, Day, DoseLog, FoodEntry, LabTest, Meal, ProtocolItem, Workout, WorkoutSet
from app.services.common import default_user_id, dto
from app.services.nutrition import add_nutrients
from app.services.workouts import epley_1rm

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/calendar")
async def calendar(month: str = Query(description="YYYY-MM")) -> list[dict]:
    user_id = await default_user_id()
    year, month_num = (int(value) for value in month.split("-"))
    first = date(year, month_num, 1)
    next_month = date(year + (month_num == 12), 1 if month_num == 12 else month_num + 1, 1)
    days = await Day.find({"user_id": user_id, "date": {"$gte": first, "$lt": next_month}}).to_list()
    labs = await LabTest.find({"user_id": user_id, "date": {"$gte": first, "$lt": next_month}}).to_list()
    lab_dates = {item.date for item in labs}
    response = []
    for day_item in days:
        color = "#374151"
        if day_item.closed and day_item.completion_pct >= 100:
            color = "#10B981"
        elif day_item.completion_pct > 0:
            color = "#F59E0B"
        if day_item.closed and day_item.completion_pct < 100:
            color = "#EF4444"
        if day_item.date in lab_dates:
            color = "#A78BFA"
        response.append({**dto(day_item), "color": color, "has_lab": day_item.date in lab_dates})
    return response


@router.get("/weight")
async def weight(from_: date = Query(alias="from"), to: date = Query()) -> dict:
    user_id = await default_user_id()
    values = await BodyMetric.find({"user_id": user_id, "date": {"$gte": from_, "$lte": to}}).sort("+date").to_list()
    points = [{"date": item.date, "weight_kg": item.weight_kg} for item in values]
    def average(period: int) -> list[dict]:
        return [{"date": values[index].date, "value": round(sum(item.weight_kg for item in values[max(0, index-period+1):index+1]) / min(index+1, period), 2)} for index in range(len(values))]
    delta = round(values[-1].weight_kg - values[0].weight_kg, 2) if len(values) > 1 else 0
    return {"points": points, "ma7": average(7), "ma30": average(30), "delta": delta}


@router.get("/training")
async def training(from_: date = Query(alias="from"), to: date = Query()) -> dict:
    user_id = await default_user_id()
    workouts = await Workout.find({"user_id": user_id, "date": {"$gte": from_, "$lte": to}}).to_list()
    weekly: dict[str, float] = defaultdict(float)
    for workout in workouts:
        monday = workout.date - timedelta(days=workout.date.weekday())
        weekly[monday.isoformat()] += workout.total_tonnage
    sets = await WorkoutSet.find({"workout_id": {"$in": [workout.id for workout in workouts]}}).to_list() if workouts else []
    growth: dict[str, float] = defaultdict(float)
    for item in sets:
        growth[str(item.exercise_id)] = max(growth[str(item.exercise_id)], epley_1rm(item.weight_kg, item.reps))
    return {"weekly_tonnage": [{"week": week, "tonnage": round(total, 2)} for week, total in sorted(weekly.items())], "workout_count": len(workouts), "top_exercises": [{"exercise_id": exercise, "best_1rm": one_rm} for exercise, one_rm in sorted(growth.items(), key=lambda value: value[1], reverse=True)[:5]]}


@router.get("/nutrition")
async def nutrition(from_: date = Query(alias="from"), to: date = Query()) -> dict:
    user_id = await default_user_id()
    meals = await Meal.find({"user_id": user_id, "date": {"$gte": from_, "$lte": to}}).to_list()
    daily: dict[date, list] = defaultdict(list)
    for meal in meals:
        daily[meal.date].extend(await FoodEntry.find(FoodEntry.meal_id == meal.id).to_list())
    summaries = [{"date": day_date, **add_nutrients([entry.nutrients for entry in entries]).model_dump()} for day_date, entries in sorted(daily.items())]
    keys = ["kcal", "protein_g", "fat_g", "carbs_g"]
    averages = {key: round(sum(row[key] or 0 for row in summaries) / len(summaries), 2) if summaries else 0 for key in keys}
    goal = get_settings().nutrition_goals["kcal"]
    return {"daily": summaries, "averages": averages, "over_calorie_days": [row["date"] for row in summaries if row["kcal"] > goal]}


@router.get("/protocol")
async def protocol(from_: date = Query(alias="from"), to: date = Query()) -> dict:
    user_id = await default_user_id()
    items = await ProtocolItem.find(ProtocolItem.user_id == user_id, ProtocolItem.archived == False).to_list()
    logs = await DoseLog.find({"user_id": user_id, "date": {"$gte": from_, "$lte": to}}).to_list()
    days = max((to - from_).days + 1, 1)
    expected = sum(1 for item in items for offset in range(days) if item.is_required and item.start_date <= from_ + timedelta(days=offset) and (not item.end_date or item.end_date >= from_ + timedelta(days=offset)) and (not item.weekdays or (from_ + timedelta(days=offset)).isoweekday() in item.weekdays))
    taken = len({(log.item_id, log.date) for log in logs if log.status == "taken"})
    misses = []
    for item in items:
        expected_item = sum(1 for offset in range(days) if item.is_required and (not item.weekdays or (from_ + timedelta(days=offset)).isoweekday() in item.weekdays))
        actual = len({log.date for log in logs if log.item_id == item.id and log.status == "taken"})
        if expected_item > actual:
            misses.append({"item": item.name, "missed": expected_item - actual})
    return {"completion_pct": round(taken / expected * 100, 1) if expected else 100, "top_missed": sorted(misses, key=lambda value: value["missed"], reverse=True), "stock_warnings": [{"name": item.name, "stock_remaining": item.stock_remaining} for item in items if item.stock_remaining is not None and item.stock_remaining <= 7]}
