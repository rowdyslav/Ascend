from beanie import PydanticObjectId

from app.models import Workout, WorkoutSet


def epley_1rm(weight_kg: float, reps: int) -> float:
    return round(weight_kg * (1 + reps / 30), 2)


async def recalculate_tonnage(workout: Workout) -> float:
    sets = await WorkoutSet.find(WorkoutSet.workout_id == workout.id).to_list()
    tonnage = sum(item.weight_kg * item.reps for item in sets if not item.is_warmup)
    workout.total_tonnage = round(tonnage, 2)
    await workout.save()
    return workout.total_tonnage


async def exercise_previous_max(exercise_id: PydanticObjectId, before_workout_id: PydanticObjectId | None = None) -> float:
    sets = await WorkoutSet.find(WorkoutSet.exercise_id == exercise_id).to_list()
    if before_workout_id:
        sets = [item for item in sets if item.workout_id != before_workout_id]
    return max((epley_1rm(item.weight_kg, item.reps) for item in sets), default=0.0)
