from datetime import date, datetime
from typing import Optional

from beanie import Document, PydanticObjectId
from pymongo import IndexModel, ASCENDING


class Day(Document):
    user_id: PydanticObjectId
    date: date
    day_type: str = "training"
    completion_pct: float = 0.0
    closed: bool = False
    close_reason: Optional[str] = None
    updated_at: datetime = datetime.utcnow()

    class Settings:
        name = "days"
        indexes = [IndexModel([("user_id", ASCENDING), ("date", ASCENDING)], unique=True)]
