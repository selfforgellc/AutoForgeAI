
from fastapi import APIRouter
from core.api_response import success

router = APIRouter()

@router.get("/explainability/info")
def explainability_info():
    return success({
        "description": "MTI 3.0 Explainability Engine provides detailed reasoning for confidence scoring and severity escalation decisions."
    })
