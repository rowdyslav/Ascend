from collections import defaultdict
from datetime import date

from fastapi import APIRouter, HTTPException, Query

from app.core.config import get_settings
from app.models import BodyMetric, Day, DoseLog, FoodEntry, LabTest, Meal, ProtocolItem
from app.services.common import default_user_id, dto
from app.services.nutrition import add_nutrients
from app.services.protocol import expected_doses_for

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/calendar")
async def calendar(month: str = Query(description="YYYY-MM")) -> list[dict]:
    user_id = await default_user_id()
    try:
        first = date.fromisoformat(month + "-01")
    except ValueError:
        raise HTTPException(status_code=422, detail="month must be in YYYY-MM format")
    next_month = date(first.year + (first.month == 12), 1 if first.month == 12 else first.month + 1, 1)
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


@router.get("/nutrition")
async def nutrition(from_: date = Query(alias="from"), to: date = Query()) -> dict:
    user_id = await default_user_id()
    meals = await Meal.find({"user_id": user_id, "date": {"$gte": from_, "$lte": to}}).to_list()
    date_by_meal = {meal.id: meal.date for meal in meals}
    entries = await FoodEntry.find({"meal_id": {"$in": list(date_by_meal)}}).to_list() if date_by_meal else []
    daily: dict[date, list] = defaultdict(list)
    for entry in entries:
        daily[date_by_meal[entry.meal_id]].append(entry)
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
    expected = sum(expected_doses_for(item, from_, to) for item in items)
    taken = len({(log.item_id, log.date) for log in logs if log.status == "taken"})
    misses = []
    for item in items:
        expected_item = expected_doses_for(item, from_, to)
        actual = len({log.date for log in logs if log.item_id == item.id and log.status == "taken"})
        if expected_item > actual:
            misses.append({"item": item.name, "missed": expected_item - actual})
    return {"completion_pct": round(taken / expected * 100, 1) if expected else 100, "top_missed": sorted(misses, key=lambda value: value["missed"], reverse=True), "stock_warnings": [{"name": item.name, "stock_remaining": item.stock_remaining} for item in items if item.stock_remaining is not None and item.stock_remaining <= 7]}
