from fastapi import APIRouter, Depends
from sqlmodel import Session, select
from db import get_session
from models import Vehicle
from core.response import ok

router = APIRouter()

@router.post("/vehicles")
def create(vehicle: Vehicle, session: Session = Depends(get_session)):
    session.add(vehicle)
    session.commit()
    session.refresh(vehicle)
    return ok(vehicle)

@router.get("/vehicles")
def all(session: Session = Depends(get_session)):
    return ok(session.exec(select(Vehicle)).all())
