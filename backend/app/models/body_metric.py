from datetime import date
from typing import Optional

from beanie import Document, PydanticObjectId
from pymongo import IndexModel, ASCENDING


class BodyMetric(Document):
    user_id: PydanticObjectId
    date: date
    weight_kg: float
    sleep_hours: Optional[float] = None
    sleep_quality: Optional[int] = None
    wellbeing: Optional[int] = None
    energy: Optional[int] = None
    appetite: Optional[int] = None
    mood: Optional[int] = None

    class Settings:
        name = "body_metrics"
        indexes = [IndexModel([("user_id", ASCENDING), ("date", ASCENDING)], unique=True)]
