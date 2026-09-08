from datetime import date

from fastapi import APIRouter, HTTPException, Query

from app.core.config import get_settings
from app.models import Food, FoodEntry, Meal
from app.schemas import FoodEntryIn, FoodIn, MealIn
from app.services.common import default_user_id, dto, get_document, object_id
from app.services.days import refresh_completion
from app.services.nutrition import add_nutrients, scale_nutrients

router = APIRouter(tags=["nutrition"])


@router.get("/foods/search")
async def search_foods(q: str = "") -> list[dict]:
    query = {"name": {"$regex": q, "$options": "i"}} if q else {}
    return [dto(item) for item in await Food.find(query).sort("+name").limit(30).to_list()]


@router.post("/foods")
async def create_food(payload: FoodIn) -> dict:
    food = Food(**payload.model_dump())
    await food.insert()
    return dto(food)


@router.get("/meals")
async def list_meals(day_date: date = Query(alias="date")) -> list[dict]:
    user_id = await default_user_id()
    meals = await Meal.find(Meal.user_id == user_id, Meal.date == day_date).sort("+meal_type").to_list()
    meal_ids = [meal.id for meal in meals]
    entries_by_meal: dict = {}
    if meal_ids:
        for entry in await FoodEntry.find({"meal_id": {"$in": meal_ids}}).to_list():
            entries_by_meal.setdefault(entry.meal_id, []).append(entry)
    response = []
    for meal in meals:
        entries = entries_by_meal.get(meal.id, [])
        response.append({**dto(meal), "entry_count": len(entries), "nutrients": add_nutrients([entry.nutrients for entry in entries]).model_dump()})
    return response


@router.post("/meals")
async def create_meal(payload: MealIn) -> dict:
    user_id = await default_user_id()
    existing = await Meal.find_one(Meal.user_id == user_id, Meal.date == payload.date, Meal.meal_type == payload.meal_type)
    if existing:
        return dto(existing)
    meal = Meal(user_id=user_id, **payload.model_dump())
    await meal.insert()
    return dto(meal)


@router.post("/meals/{meal_id}/entries")
async def add_entry(meal_id: str, payload: FoodEntryIn) -> dict:
    meal = await get_document(Meal, meal_id)
    food = await get_document(Food, payload.food_id)
    entry = FoodEntry(meal_id=meal.id, food_id=food.id, weight_g=payload.weight_g, nutrients=scale_nutrients(food.per_100g, payload.weight_g))
    await entry.insert()
    await refresh_completion(meal.user_id, meal.date)
    return {**dto(entry), "food": dto(food)}


@router.get("/meals/{meal_id}/entries")
async def list_entries(meal_id: str) -> list[dict]:
    meal = await get_document(Meal, meal_id)
    entries = await FoodEntry.find(FoodEntry.meal_id == meal.id).to_list()
    food_ids = [entry.food_id for entry in entries]
    foods = {food.id: food for food in await Food.find({"_id": {"$in": food_ids}}).to_list()} if food_ids else {}
    return [{**dto(entry), "food": dto(foods[entry.food_id]) if entry.food_id in foods else None} for entry in entries]


@router.get("/nutrition/daily-diary")
async def daily_diary(day_date: date = Query(alias="date")) -> dict:
    """One aggregated call: day totals/goals + meals with their entries embedded."""
    user_id = await default_user_id()
    meals = await Meal.find(Meal.user_id == user_id, Meal.date == day_date).sort("+meal_type").to_list()
    meal_ids = [meal.id for meal in meals]
    all_entries = await FoodEntry.find({"meal_id": {"$in": meal_ids}}).to_list() if meal_ids else []
    food_ids = {entry.food_id for entry in all_entries}
    foods = {food.id: food for food in await Food.find({"_id": {"$in": list(food_ids)}}).to_list()} if food_ids else {}
    entries_by_meal: dict = {}
    for entry in all_entries:
        entries_by_meal.setdefault(entry.meal_id, []).append(entry)
    meals_out = []
    for meal in meals:
        entries = entries_by_meal.get(meal.id, [])
        meals_out.append({
            **dto(meal),
            "entries": [{**dto(entry), "food": dto(foods[entry.food_id]) if entry.food_id in foods else None} for entry in entries],
        })
    totals = add_nutrients([entry.nutrients for entry in all_entries])
    goals = get_settings().nutrition_goals
    remaining = {key: round(max(0, value - (getattr(totals, key) or 0)), 2) for key, value in goals.items() if hasattr(totals, key)}
    percent = {key: round(((getattr(totals, key) or 0) / value) * 100, 1) for key, value in goals.items() if value and hasattr(totals, key)}
    return {"date": day_date, "totals": totals.model_dump(), "goals": goals, "remaining": remaining, "percent": percent, "meals": meals_out}


@router.delete("/entries/{entry_id}")
async def delete_entry(entry_id: str) -> dict:
    entry = await get_document(FoodEntry, entry_id)
    meal = await get_document(Meal, str(entry.meal_id))
    await entry.delete()
    await refresh_completion(meal.user_id, meal.date)
    return {"deleted": True}
