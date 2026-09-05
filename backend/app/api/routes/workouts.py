from datetime import date, timedelta

from fastapi import APIRouter, HTTPException, Query

from app.models import Exercise, Workout, WorkoutSet
from app.schemas import ExerciseIn, WorkoutIn, WorkoutSetIn, WorkoutUpdate
from app.services.common import default_user_id, dto, get_document, object_id
from app.services.days import refresh_completion
from app.services.workouts import epley_1rm, exercise_previous_max, recalculate_tonnage

router = APIRouter(tags=["workouts"])


@router.get("/workouts/week")
async def week_plan(date_: date = Query(alias="date")) -> list[dict]:
    user_id = await default_user_id()
    monday = date_ - timedelta(days=date_.weekday())
    sunday = monday + timedelta(days=6)
    items = await Workout.find({"user_id": user_id, "date": {"$gte": monday, "$lte": sunday}}).sort("+date").to_list()
    return [dto(item) for item in items]


@router.post("/workouts")
async def create_workout(payload: WorkoutIn) -> dict:
    user_id = await default_user_id()
    workout = Workout(user_id=user_id, **payload.model_dump())
    await workout.insert()
    await refresh_completion(user_id, workout.date)
    return dto(workout)


@router.put("/workouts/{workout_id}")
async def update_workout(workout_id: str, payload: WorkoutUpdate) -> dict:
    workout = await get_document(Workout, workout_id)
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(workout, key, value)
    await workout.save()
    await refresh_completion(workout.user_id, workout.date)
    return dto(workout)


@router.get("/workouts/{workout_id}")
async def get_workout(workout_id: str) -> dict:
    return dto(await get_document(Workout, workout_id))


@router.post("/workouts/{workout_id}/sets")
async def create_set(workout_id: str, payload: WorkoutSetIn) -> dict:
    workout = await get_document(Workout, workout_id)
    exercise_id = object_id(payload.exercise_id)
    if not await Exercise.get(exercise_id):
        raise HTTPException(status_code=404, detail="Exercise not found")
    previous = await exercise_previous_max(exercise_id, workout.id)
    workout_set = WorkoutSet(workout_id=workout.id, exercise_id=exercise_id, **payload.model_dump(exclude={"exercise_id"}))
    await workout_set.insert()
    await recalculate_tonnage(workout)
    one_rm = epley_1rm(workout_set.weight_kg, workout_set.reps)
    return {**dto(workout_set), "one_rm": one_rm, "is_pr": one_rm > previous}


@router.get("/workouts/{workout_id}/sets")
async def list_sets(workout_id: str) -> list[dict]:
    workout = await get_document(Workout, workout_id)
    items = await WorkoutSet.find(WorkoutSet.workout_id == workout.id).sort("+order", "+set_number").to_list()
    return [{**dto(item), "one_rm": epley_1rm(item.weight_kg, item.reps)} for item in items]


@router.get("/exercises")
async def list_exercises() -> list[dict]:
    user_id = await default_user_id()
    return [dto(item) for item in await Exercise.find(Exercise.user_id == user_id).sort("+name").to_list()]


@router.post("/exercises")
async def create_exercise(payload: ExerciseIn) -> dict:
    item = Exercise(user_id=await default_user_id(), **payload.model_dump())
    await item.insert()
    return dto(item)


@router.get("/exercises/{exercise_id}/history")
async def exercise_history(exercise_id: str) -> list[dict]:
    exercise = await get_document(Exercise, exercise_id)
    sets = await WorkoutSet.find(WorkoutSet.exercise_id == exercise.id).sort("-id").to_list()
    workout_ids = {item.workout_id for item in sets}
    workouts = {item.id: item for item in await Workout.find({"_id": {"$in": list(workout_ids)}}).to_list()}
    return [{**dto(item), "workout_date": workouts.get(item.workout_id).date if item.workout_id in workouts else None, "one_rm": epley_1rm(item.weight_kg, item.reps)} for item in sets]
