from datetime import date, time
from typing import Optional

from beanie import Document, PydanticObjectId
from pymongo import IndexModel, ASCENDING


class ProtocolItem(Document):
    user_id: PydanticObjectId
    name: str
    category: str
    planned_dose_value: float
    planned_dose_unit: str
    schedule_times: list[time] = []
    weekdays: list[int] = []
    route: Optional[str] = None
    default_site: Optional[str] = None
    start_date: date
    end_date: Optional[date] = None
    stock_remaining: Optional[float] = None
    is_required: bool = True
    archived: bool = False

    class Settings:
        name = "protocol_items"
        indexes = ["user_id"]


class DoseLog(Document):
    user_id: PydanticObjectId
    item_id: PydanticObjectId
    date: date
    time: time
    actual_dose_value: float
    actual_dose_unit: str
    status: str = "taken"
    site: Optional[str] = None
    side: Optional[str] = None
    reaction: Optional[str] = None
    comment: Optional[str] = None
    confirmed: bool = True

    class Settings:
        name = "dose_logs"
        indexes = [IndexModel([("item_id", ASCENDING), ("date", ASCENDING), ("time", ASCENDING)])]
