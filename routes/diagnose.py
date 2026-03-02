
from fastapi import Depends
from core.auth import enforce_usage_limit

from core.metrics import DIAGNOSIS_COUNT

from fastapi import APIRouter
from pydantic import BaseModel
from core.api_response import success, failure
from services.async_orchestrator import async_diagnosis

router = APIRouter()

class DiagnoseRequest(BaseModel):
    vehicle_id: str
    symptoms: list[str] | None = None
    chat_input: str | None = None
    obd_codes: list[str] | None = None

@router.post("/diagnose", dependencies=[Depends(enforce_usage_limit)])
async def diagnose(body: DiagnoseRequest):

    result = await async_diagnosis(
        vehicle_id=body.vehicle_id,
        symptoms=body.symptoms,
        chat_input=body.chat_input,
        obd_codes=body.obd_codes
    )

    if not result:
        return failure("No diagnostic input provided.")

    
    DIAGNOSIS_COUNT.inc()
    return success(result)

