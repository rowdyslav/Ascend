import asyncio
import datetime as _datetime

from beanie import PydanticObjectId, init_beanie
from beanie.odm.utils.encoder import DEFAULT_CUSTOM_ENCODERS
from motor.motor_asyncio import AsyncIOMotorClient

from app.core.config import get_settings
from app.models import ALL_MODELS, User
from app.services.seed import seed_database

_client: AsyncIOMotorClient | None = None


def configure_encoders() -> None:
    """Teach Beanie to serialize `datetime.time` fields.

    Beanie 1.x knows `date` and `timedelta` but not `time`, so we store times as
    "HH:MM:SS" strings; Pydantic coerces them back into `time` on read.

    WARNING: this mutates a beanie-internal dict (DEFAULT_CUSTOM_ENCODERS).
    On every beanie upgrade, verify that time fields still round-trip correctly.
    """
    DEFAULT_CUSTOM_ENCODERS[_datetime.time] = lambda value: value.strftime("%H:%M:%S")


async def init_db() -> None:
    global _client
    settings = get_settings()
    configure_encoders()
    _client = AsyncIOMotorClient(settings.mongodb_uri, serverSelectionTimeoutMS=3000)
    # Compose can need a few seconds before Mongo begins accepting connections.
    for attempt in range(20):
        try:
            await _client.admin.command("ping")
            break
        except Exception:
            if attempt == 19:
                raise
            await asyncio.sleep(1)
    await init_beanie(database=_client[settings.mongodb_db], document_models=ALL_MODELS)
    user_id = PydanticObjectId(settings.default_user_id)
    if not await User.get(user_id):
        await User(id=user_id, name="ASCEND User").insert()
    await seed_database(user_id)


async def close_db() -> None:
    if _client is not None:
        _client.close()
