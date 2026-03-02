
from sqlmodel import select
from models.fleet import FleetVehicle
from models.issue import IssueStatus
from services.vhi_engine import calculate_vhi
from services.predictive_engine import predict_failure_probability
from services.economic_compound_engine import compute_compounded_risk, neglect_penalty
from models.decision import Decision
from db import get_session

def compute_fleet_vhi(fleet_id: str):
    with next(get_session()) as session:
        fleet_links = session.exec(
            select(FleetVehicle).where(FleetVehicle.fleet_id == fleet_id)
        ).all()

        vehicle_ids = [f.vehicle_id for f in fleet_links]

        total_vhi = 0
        vehicle_count = len(vehicle_ids)

        for vehicle_id in vehicle_ids:
            issues = session.exec(
                select(IssueStatus).where(IssueStatus.vehicle_id == vehicle_id, IssueStatus.resolved == False)
            ).all()

            decisions = session.exec(
                select(Decision).where(Decision.vehicle_id == vehicle_id)
            ).all()

            open_issue_count = len(issues)
            critical_count = sum(1 for i in issues if i.severity == "critical")
            total_ignored = sum(1 for d in decisions if d.decision_type == "ignore")

            failure_probs = [
                predict_failure_probability(i.severity, i.created_at)
                for i in issues
            ]

            compounded = [
                compute_compounded_risk(i.severity, i.created_at, open_issue_count)
                for i in issues
            ]

            penalty = neglect_penalty(total_ignored)

            vhi_score = calculate_vhi(
                open_issue_count,
                critical_count,
                failure_probs,
                compounded,
                penalty
            )

            total_vhi += vhi_score

        if vehicle_count == 0:
            return 0

        return round(total_vhi / vehicle_count, 2)
