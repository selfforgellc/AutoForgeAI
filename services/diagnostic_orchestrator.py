
from diag_engine import run_diagnosis
from models_mti import MTIResponse, ConfidenceBreakdown, SeverityLevel
import random

def classify_severity(confidence: float, related_systems: list):
    if "braking" in related_systems or "steering" in related_systems:
        return SeverityLevel.critical
    if confidence < 0.4:
        return SeverityLevel.moderate
    return SeverityLevel.low

def build_confidence_breakdown(confidence: float, symptoms, obd_codes):
    symptom_score = 0.8 if symptoms else 0.3
    obd_score = 0.9 if obd_codes else 0.0
    knowledge_score = confidence
    historical_score = 0.6
    return ConfidenceBreakdown(
        symptom_match_score=symptom_score,
        obd_match_score=obd_score,
        knowledge_match_score=knowledge_score,
        historical_similarity_score=historical_score
    )

def run_orchestrator(vehicle_id, symptoms=None, chat_input=None, obd_codes=None, context=None):
    result = run_diagnosis(
        vehicle_id=vehicle_id,
        symptoms=symptoms,
        chat_input=chat_input,
        obd_codes=obd_codes,
        context=context
    )

    if not result:
        return None

    confidence = result["confidence"]
    related_systems = result.get("related_systems", [])

    base_severity = classify_severity(confidence, related_systems)
    unresolved_count, ignored_count = compute_unresolved(vehicle_id)
    severity = escalate_severity(base_severity.value, related_systems, unresolved_count, ignored_count)
    drive_safe = severity != SeverityLevel.critical

    breakdown = build_confidence_breakdown(confidence, symptoms, obd_codes)

    modifier = compute_historical_modifier(vehicle_id, related_systems)
    
    historical_score = modifier
    confidence = compute_weighted_confidence(confidence, symptoms, obd_codes, historical_score, severity)

    uncertainty = round(1 - confidence, 2)

    transparency = build_transparency(severity, confidence)

    return MTIResponse(
        diagnosis_id=result["diagnosis_id"],
        recommendation=result["recommendation"],
        confidence=confidence,
        confidence_breakdown=breakdown,
        severity=severity,
        drive_safe=drive_safe,
        related_systems=related_systems,
        reasoning_summary=result["recommendation"],
        uncertainty_percentage=uncertainty
    )

from sqlmodel import Session, select
from db import get_session
from models_phase2 import TimelineEvent

def calculate_historical_similarity(vehicle_id: str):
    with get_session() as session:
        results = session.exec(
            select(TimelineEvent).where(TimelineEvent.vehicle_id == vehicle_id)
        ).all()

        if not results:
            return 0.3

        return min(0.9, 0.3 + (len(results) * 0.05))

from sqlmodel import select
from models_phase2 import TimelineEvent, Decision
from db import get_session

def compute_historical_modifier(vehicle_id: str, related_systems: list):
    with get_session() as session:
        events = session.exec(
            select(TimelineEvent).where(TimelineEvent.vehicle_id == vehicle_id)
        ).all()

        decisions = session.exec(
            select(Decision).where(Decision.vehicle_id == vehicle_id)
        ).all()

    repeat_factor = min(len(events) * 0.03, 0.2)

    ignored_critical = 0
    for d in decisions:
        if d.decision_type == "ignore":
            ignored_critical += 1

    ignore_penalty = min(ignored_critical * 0.05, 0.25)

    modifier = 1 - ignore_penalty + repeat_factor
    return max(0.6, min(modifier, 1.2))

from services.severity_engine import escalate_severity
from services.transparency_engine import build_transparency
from models_issue_status import IssueStatus
from models_phase2 import Decision
from sqlmodel import select
from db import get_session

def compute_unresolved(vehicle_id: str):
    with get_session() as session:
        issues = session.exec(select(IssueStatus).where(IssueStatus.vehicle_id == vehicle_id, IssueStatus.resolved == False)).all()
        decisions = session.exec(select(Decision).where(Decision.vehicle_id == vehicle_id)).all()

    ignored = sum(1 for d in decisions if d.decision_type == "ignore")
    return len(issues), ignored

def compute_weighted_confidence(base_confidence, symptoms, obd_codes, historical_score, severity):
    knowledge_score = base_confidence
    symptom_score = 0.9 if symptoms else 0.4
    obd_score = 0.95 if obd_codes else 0.0
    system_risk_score = 1.0 if severity == "critical" else 0.7 if severity == "moderate" else 0.4

    confidence = (
        knowledge_score * 0.35 +
        symptom_score * 0.20 +
        obd_score * 0.20 +
        historical_score * 0.15 +
        system_risk_score * 0.10
    )

    return max(0.0, min(confidence, 1.0))
