from datetime import date

from fastapi import APIRouter, Query

from app.models import BodyMetric
from app.schemas import BodyMetricIn
from app.services.common import default_user_id, dto
from app.services.days import refresh_completion

router = APIRouter(prefix="/body-metrics", tags=["body metrics"])


@router.get("")
async def list_metrics(from_: date | None = Query(default=None, alias="from"), to: date | None = None) -> list[dict]:
    user_id = await default_user_id()
    query = {"user_id": user_id}
    if from_ or to:
        query["date"] = {**({"$gte": from_} if from_ else {}), **({"$lte": to} if to else {})}
    return [dto(item) for item in await BodyMetric.find(query).sort("+date").to_list()]


@router.post("")
async def create_metric(payload: BodyMetricIn) -> dict:
    user_id = await default_user_id()
    current = await BodyMetric.find_one(BodyMetric.user_id == user_id, BodyMetric.date == payload.date)
    if current:
        for key, value in payload.model_dump().items():
            setattr(current, key, value)
        await current.save()
        item = current
    else:
        item = BodyMetric(user_id=user_id, **payload.model_dump())
        await item.insert()
    await refresh_completion(user_id, payload.date)
    return dto(item)
