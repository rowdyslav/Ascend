from fastapi import APIRouter, Query

from app.models import LabMarker, LabTest
from app.schemas import LabCompareIn, LabMarkerIn, LabTestIn
from app.services.common import default_user_id, dto, get_document, object_id

router = APIRouter(prefix="/lab", tags=["lab"])


def marker_flag(value: float, ref_min: float | None, ref_max: float | None) -> str | None:
    if ref_min is not None and value < ref_min:
        return "low"
    if ref_max is not None and value > ref_max:
        return "high"
    return "normal" if ref_min is not None or ref_max is not None else None


@router.get("/tests")
async def list_tests() -> list[dict]:
    user_id = await default_user_id()
    tests = await LabTest.find(LabTest.user_id == user_id).sort("-date").to_list()
    response = []
    for test in tests:
        markers = await LabMarker.find(LabMarker.test_id == test.id).to_list()
        response.append({**dto(test), "marker_count": len(markers), "markers": [dto(marker) for marker in markers]})
    return response


@router.post("/tests")
async def create_test(payload: LabTestIn) -> dict:
    test = LabTest(user_id=await default_user_id(), **payload.model_dump())
    await test.insert()
    return dto(test)


@router.post("/tests/{test_id}/markers")
async def add_marker(test_id: str, payload: LabMarkerIn) -> dict:
    test = await get_document(LabTest, test_id)
    marker = LabMarker(test_id=test.id, **payload.model_dump(), flag=marker_flag(payload.value, payload.ref_min, payload.ref_max))
    await marker.insert()
    return dto(marker)


@router.get("/markers/history")
async def marker_history(name: str = Query()) -> list[dict]:
    user_id = await default_user_id()
    tests = await LabTest.find(LabTest.user_id == user_id).to_list()
    tests_by_id = {test.id: test for test in tests}
    markers = await LabMarker.find({"test_id": {"$in": list(tests_by_id)}, "name": {"$regex": f"^{name}$", "$options": "i"}}).to_list()
    return [{**dto(marker), "test_date": tests_by_id[marker.test_id].date, "panel_name": tests_by_id[marker.test_id].panel_name} for marker in sorted(markers, key=lambda item: tests_by_id[item.test_id].date)]


@router.post("/compare")
async def compare(payload: LabCompareIn) -> list[dict]:
    ids = [object_id(item) for item in payload.test_ids]
    tests = {test.id: test for test in await LabTest.find({"_id": {"$in": ids}}).to_list()}
    markers = await LabMarker.find({"test_id": {"$in": ids}, "name": {"$regex": f"^{payload.marker}$", "$options": "i"}}).to_list()
    return [{**dto(marker), "test_date": tests[marker.test_id].date, "panel_name": tests[marker.test_id].panel_name} for marker in sorted(markers, key=lambda item: tests[item.test_id].date)]
