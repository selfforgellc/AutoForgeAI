from fastapi import APIRouter, Depends
from sqlmodel import Session, select
from db import get_session
from models import Diagnosis
from core.response import ok

router = APIRouter()

@router.get("/history/{vehicle_id}")
def history(vehicle_id: str, session: Session = Depends(get_session)):
    records = session.exec(
        select(Diagnosis).where(Diagnosis.vehicle_id == vehicle_id)
    ).all()
    return ok(records)
