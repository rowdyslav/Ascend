import logging
from datetime import date, datetime

from fastapi import APIRouter, HTTPException, Query

from app.models import DoseLog, ProtocolItem
from app.schemas import DoseLogIn, ProtocolItemIn, ProtocolItemUpdate
from app.services.common import default_user_id, dto, get_document
from app.services.days import refresh_completion
from app.services.protocol import item_is_due

router = APIRouter(prefix="/protocol", tags=["protocol"])
logger = logging.getLogger("ascend.protocol")


@router.get("/items")
async def list_items() -> list[dict]:
    user_id = await default_user_id()
    return [dto(item) for item in await ProtocolItem.find(ProtocolItem.user_id == user_id, ProtocolItem.archived == False).sort("+name").to_list()]


@router.post("/items")
async def create_item(payload: ProtocolItemIn) -> dict:
    item = ProtocolItem(user_id=await default_user_id(), **payload.model_dump())
    await item.insert()
    return dto(item)


@router.put("/items/{item_id}")
async def update_item(item_id: str, payload: ProtocolItemUpdate) -> dict:
    item = await get_document(ProtocolItem, item_id)
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(item, key, value)
    await item.save()
    return dto(item)


@router.get("/items/{item_id}/schedule")
async def schedule(item_id: str, day_date: date = Query(alias="date")) -> dict:
    item = await get_document(ProtocolItem, item_id)
    logs = await DoseLog.find(DoseLog.item_id == item.id, DoseLog.date == day_date).sort("+time").to_list()
    return {"item": dto(item), "date": day_date, "due": item_is_due(item, day_date), "scheduled_times": item.schedule_times, "logs": [dto(log) for log in logs]}


@router.post("/items/{item_id}/log")
async def log_dose(item_id: str, payload: DoseLogIn) -> dict:
    item = await get_document(ProtocolItem, item_id)
    now = datetime.now()
    logged_time = payload.time or now.time().replace(microsecond=0)
    logged_date = now.date()
    logs = await DoseLog.find(DoseLog.item_id == item.id, DoseLog.date == logged_date).to_list()
    proposed = datetime.combine(logged_date, logged_time)
    duplicate = next((log for log in logs if abs((datetime.combine(logged_date, log.time) - proposed).total_seconds()) <= 300), None)
    if duplicate and not payload.force_duplicate:
        raise HTTPException(status_code=409, detail={"message": f"Уже отмечено в {duplicate.time.strftime('%H:%M')}", "existing_log_id": str(duplicate.id)})
    log = DoseLog(
        user_id=item.user_id, item_id=item.id, date=logged_date, time=logged_time,
        actual_dose_value=payload.actual_dose_value if payload.actual_dose_value is not None else item.planned_dose_value,
        actual_dose_unit=payload.actual_dose_unit or item.planned_dose_unit,
        status=payload.status, site=payload.site or item.default_site, side=payload.side,
        reaction=payload.reaction, comment=payload.comment, confirmed=payload.confirmed,
    )
    await log.insert()
    if item.stock_remaining is not None and payload.status == "taken":
        if log.actual_dose_unit == item.planned_dose_unit:
            item.stock_remaining = max(0, item.stock_remaining - log.actual_dose_value)
            await item.save()
        else:
            logger.warning(
                "Stock not decremented for %s: dose unit %s != planned unit %s",
                item.name, log.actual_dose_unit, item.planned_dose_unit,
            )
    await refresh_completion(item.user_id, logged_date)
    return dto(log)


@router.get("/items/{item_id}/history")
async def item_history(item_id: str) -> list[dict]:
    item = await get_document(ProtocolItem, item_id)
    return [dto(log) for log in await DoseLog.find(DoseLog.item_id == item.id).sort("-date", "-time").to_list()]


@router.get("/rotation")
async def injection_rotation() -> dict:
    user_id = await default_user_id()
    zones = ["дельта Л", "дельта П", "бицепс Л", "бицепс П", "квад Л", "квад П", "ягодица Л", "ягодица П", "живот", "бедро Л", "бедро П", "живот низ"]
    logs = await DoseLog.find(DoseLog.user_id == user_id, DoseLog.site != None).to_list()
    last_use = {zone: max((log.date for log in logs if log.site == zone), default=None) for zone in zones}
    suggestion = min(zones, key=lambda zone: last_use[zone] or date.min)
    return {"zones": {zone: last_use[zone] for zone in zones}, "suggestion": suggestion}


@router.get("/sites/{site}/history")
async def site_history(site: str) -> list[dict]:
    user_id = await default_user_id()
    return [dto(log) for log in await DoseLog.find(DoseLog.user_id == user_id, DoseLog.site == site).sort("-date", "-time").to_list()]
