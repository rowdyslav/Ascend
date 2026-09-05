from datetime import date
from typing import Optional

from beanie import Document, PydanticObjectId
from pymongo import IndexModel, ASCENDING


class LabTest(Document):
    user_id: PydanticObjectId
    date: date
    panel_name: Optional[str] = None
    lab: Optional[str] = None

    class Settings:
        name = "lab_tests"
        indexes = [IndexModel([("user_id", ASCENDING), ("date", ASCENDING)])]


class LabMarker(Document):
    test_id: PydanticObjectId
    category: str
    name: str
    value: float
    unit: str
    ref_min: Optional[float] = None
    ref_max: Optional[float] = None
    flag: Optional[str] = None

    class Settings:
        name = "lab_markers"
        indexes = [IndexModel([("test_id", ASCENDING), ("name", ASCENDING)])]
