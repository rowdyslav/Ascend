from datetime import datetime

from beanie import Document
from pydantic import Field


class User(Document):
    name: str
    private_mode: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "users"
