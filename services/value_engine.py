from sqlmodel import select
from models import Diagnosis, Decision

def calculate(vehicle_id, session):
    diagnoses = session.exec(
        select(Diagnosis).where(Diagnosis.vehicle_id == vehicle_id)
    ).all()

    decisions = session.exec(
        select(Decision).where(Decision.vehicle_id == vehicle_id)
    ).all()

    fix_count = len([d for d in decisions if d.decision == "fix_now"])

    return {
        "diagnoses": len(diagnoses),
        "decisions": len(decisions),
        "estimated_saved": fix_count * 350
    }
