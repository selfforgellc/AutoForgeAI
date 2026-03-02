
from pydantic import BaseModel
from typing import List
from enum import Enum

class SeverityLevel(str, Enum):
    low = "low"
    moderate = "moderate"
    critical = "critical"

class ConfidenceBreakdown(BaseModel):
    symptom_match_score: float
    obd_match_score: float
    knowledge_match_score: float
    historical_similarity_score: float

class MTIResponse(BaseModel):
    diagnosis_id: str
    recommendation: str
    confidence: float
    confidence_breakdown: ConfidenceBreakdown
    severity: SeverityLevel
    drive_safe: bool
    related_systems: List[str]
    reasoning_summary: str
    uncertainty_percentage: float
