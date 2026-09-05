"""Request/response DTOs used by the ASCEND API."""
from datetime import date, time as Time
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.nutrition import Nutrients


class DTO(BaseModel):
    model_config = ConfigDict(extra="forbid")


class DayCloseIn(DTO):
    reason: Optional[str] = None


class BodyMetricIn(DTO):
    date: date
    weight_kg: float
    sleep_hours: Optional[float] = Field(default=None, ge=0, le=24)
    sleep_quality: Optional[int] = Field(default=None, ge=1, le=10)
    wellbeing: Optional[int] = Field(default=None, ge=1, le=10)
    energy: Optional[int] = Field(default=None, ge=1, le=10)
    appetite: Optional[int] = Field(default=None, ge=1, le=10)
    mood: Optional[int] = Field(default=None, ge=1, le=10)


class ExerciseIn(DTO):
    name: str
    muscle_group: str
    equipment: Optional[str] = None


class WorkoutIn(DTO):
    date: date
    name: str
    is_rest_day: bool = False
    completed: bool = False
    duration_min: Optional[int] = None
    difficulty: Optional[int] = Field(default=None, ge=1, le=10)
    pump: Optional[int] = Field(default=None, ge=1, le=10)
    energy_level: Optional[int] = Field(default=None, ge=1, le=10)
    pain: Optional[bool] = None
    comment: Optional[str] = None


class WorkoutUpdate(DTO):
    name: Optional[str] = None
    is_rest_day: Optional[bool] = None
    completed: Optional[bool] = None
    duration_min: Optional[int] = None
    difficulty: Optional[int] = Field(default=None, ge=1, le=10)
    pump: Optional[int] = Field(default=None, ge=1, le=10)
    energy_level: Optional[int] = Field(default=None, ge=1, le=10)
    pain: Optional[bool] = None
    comment: Optional[str] = None


class WorkoutSetIn(DTO):
    exercise_id: str
    order: int = 0
    set_number: int = 1
    weight_kg: float = Field(ge=0)
    reps: int = Field(ge=1)
    rir: Optional[int] = Field(default=None, ge=0, le=10)
    rpe: Optional[float] = Field(default=None, ge=1, le=10)
    rest_sec: Optional[int] = Field(default=None, ge=0)
    tempo: Optional[str] = None
    is_warmup: bool = False
    is_failure: bool = False
    is_dropset: bool = False
    is_superset: bool = False
    comment: Optional[str] = None


class FoodIn(DTO):
    name: str
    brand: Optional[str] = None
    barcode: Optional[str] = None
    per_100g: Nutrients
    source: str = "manual"


class MealIn(DTO):
    date: date
    meal_type: str


class FoodEntryIn(DTO):
    food_id: str
    weight_g: float = Field(gt=0)


class ProtocolItemIn(DTO):
    name: str
    category: str
    planned_dose_value: float = Field(ge=0)
    planned_dose_unit: str
    schedule_times: list[Time] = []
    weekdays: list[int] = []
    route: Optional[str] = None
    default_site: Optional[str] = None
    start_date: date
    end_date: Optional[date] = None
    stock_remaining: Optional[float] = None
    is_required: bool = True
    archived: bool = False


class ProtocolItemUpdate(DTO):
    name: Optional[str] = None
    category: Optional[str] = None
    planned_dose_value: Optional[float] = None
    planned_dose_unit: Optional[str] = None
    schedule_times: Optional[list[Time]] = None
    weekdays: Optional[list[int]] = None
    route: Optional[str] = None
    default_site: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    stock_remaining: Optional[float] = None
    is_required: Optional[bool] = None
    archived: Optional[bool] = None


class DoseLogIn(DTO):
    actual_dose_value: Optional[float] = None
    actual_dose_unit: Optional[str] = None
    time: Optional[Time] = None
    status: str = "taken"
    site: Optional[str] = None
    side: Optional[str] = None
    reaction: Optional[str] = None
    comment: Optional[str] = None
    confirmed: bool = True
    force_duplicate: bool = False


class LabTestIn(DTO):
    date: date
    panel_name: Optional[str] = None
    lab: Optional[str] = None


class LabMarkerIn(DTO):
    category: str
    name: str
    value: float
    unit: str
    ref_min: Optional[float] = None
    ref_max: Optional[float] = None


class LabCompareIn(DTO):
    marker: str
    test_ids: list[str]
