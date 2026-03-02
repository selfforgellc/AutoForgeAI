from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from db import get_session
from models.fleet import Fleet, FleetVehicle
from core.response import success
from core.auth import require_tier
from services.fleet_engine import compute_fleet_vhi

router = APIRouter()


@router.post(
    "/fleet",
    dependencies=[Depends(require_tier("enterprise"))],
)
def create_fleet(
    name: str,
    session: Session = Depends(get_session),
):
    fleet = Fleet(name=name)
    session.add(fleet)
    session.commit()
    session.refresh(fleet)

    return success({"fleet_id": fleet.id})


@router.post(
    "/fleet/{fleet_id}/add_vehicle",
    dependencies=[Depends(require_tier("enterprise"))],
)
def add_vehicle_to_fleet(
    fleet_id: str,
    vehicle_id: str,
    session: Session = Depends(get_session),
):
    link = FleetVehicle(
        fleet_id=fleet_id,
        vehicle_id=vehicle_id,
    )

    session.add(link)
    session.commit()

    return success(
        {
            "fleet_id": fleet_id,
            "vehicle_id": vehicle_id,
        }
    )


@router.get(
    "/fleet/{fleet_id}/dashboard",
    dependencies=[Depends(require_tier("enterprise"))],
)
def fleet_dashboard(fleet_id: str):
    fleet_vhi = compute_fleet_vhi(fleet_id)

    return success(
        {
            "fleet_id": fleet_id,
            "fleet_average_vhi": fleet_vhi,
        }
    )
