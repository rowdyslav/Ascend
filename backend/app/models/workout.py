from datetime import date
from typing import Optional

from beanie import Document, PydanticObjectId
from pymongo import IndexModel, ASCENDING


class Exercise(Document):
    user_id: PydanticObjectId
    name: str
    muscle_group: str
    equipment: Optional[str] = None

    class Settings:
        name = "exercises"


class Workout(Document):
    user_id: PydanticObjectId
    date: date
    name: str
    is_rest_day: bool = False
    completed: bool = False
    duration_min: Optional[int] = None
    difficulty: Optional[int] = None
    pump: Optional[int] = None
    energy_level: Optional[int] = None
    pain: Optional[bool] = None
    comment: Optional[str] = None
    total_tonnage: float = 0.0

    class Settings:
        name = "workouts"
        indexes = [IndexModel([("user_id", ASCENDING), ("date", ASCENDING)])]


class WorkoutSet(Document):
    workout_id: PydanticObjectId
    exercise_id: PydanticObjectId
    order: int
    set_number: int
    weight_kg: float
    reps: int
    rir: Optional[int] = None
    rpe: Optional[float] = None
    rest_sec: Optional[int] = None
    tempo: Optional[str] = None
    is_warmup: bool = False
    is_failure: bool = False
    is_dropset: bool = False
    is_superset: bool = False
    comment: Optional[str] = None

    class Settings:
        name = "workout_sets"
        indexes = [IndexModel([("workout_id", ASCENDING), ("order", ASCENDING), ("set_number", ASCENDING)])]
