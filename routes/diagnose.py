from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/diagnose", tags=["diagnose"])

class DiagnoseRequest(BaseModel):
    vehicle: str | None = None
    codes: list[str] | None = None
    symptoms: str | None = None
    prior_repairs: str | None = None

@router.post("")
async def diagnose(request: DiagnoseRequest):
    # Minimal test version for connectivity
    return {
        "summary": "Backend connection successful.",
        "suggestions": [
            {
                "code": "P0171",
                "title": "System Too Lean (Bank 1)",
                "common_causes": ["Vacuum leak", "Dirty MAF"],
                "first_checks": ["Smoke test", "Check MAF sensor"],
            }
        ],
        "ai_plan": f"Received: {request.vehicle} | Codes: {request.codes} | Symptoms: {request.symptoms}",
    }
