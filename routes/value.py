from fastapi import APIRouter, Depends
from sqlmodel import Session
from db import get_session
from services.value_engine import calculate
from core.response import ok

router = APIRouter()

@router.get("/value/{vehicle_id}")
def value(vehicle_id: str, session: Session = Depends(get_session)):
    return ok(calculate(vehicle_id, session))
