from typing import TypeVar

from beanie import Document, PydanticObjectId
from fastapi import HTTPException

from app.core.config import get_settings
from app.models import User

T = TypeVar("T", bound=Document)


async def default_user_id() -> PydanticObjectId:
    settings = get_settings()
    user_id = PydanticObjectId(settings.default_user_id)
    if not await User.get(user_id):
        raise HTTPException(status_code=503, detail="Default user is not initialized")
    return user_id


def object_id(value: str) -> PydanticObjectId:
    try:
        return PydanticObjectId(value)
    except Exception as exc:
        raise HTTPException(status_code=422, detail="Invalid document id") from exc


async def get_document(model: type[T], value: str) -> T:
    document = await model.get(object_id(value))
    if document is None:
        raise HTTPException(status_code=404, detail=f"{model.__name__} not found")
    return document


def dto(document: T) -> dict:
    """Convert a Beanie model to JSON-safe FastAPI content with a plain `id` key."""
    data = document.model_dump(mode="json", by_alias=True)
    if "_id" in data:
        data["id"] = data.pop("_id")
    return data
