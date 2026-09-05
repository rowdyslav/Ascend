from .user import User
from .day import Day
from .body_metric import BodyMetric
from .workout import Exercise, Workout, WorkoutSet
from .nutrition import Nutrients, Food, Meal, FoodEntry
from .protocol import ProtocolItem, DoseLog
from .lab import LabTest, LabMarker

# Nutrients is an embedded document and must not be registered with init_beanie.
ALL_MODELS = [User, Day, BodyMetric, Exercise, Workout, WorkoutSet, Food, Meal, FoodEntry, ProtocolItem, DoseLog, LabTest, LabMarker]
