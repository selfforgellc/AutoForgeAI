
from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime
import uuid

class Decision(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    vehicle_id: str
    diagnosis_id: str
    decision_type: str  # fix_now, monitor, ignore, more_info
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class TimelineEvent(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    vehicle_id: str
    event_type: str  # diagnosis, decision, value_update
    reference_id: Optional[str] = None
    payload: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class VehicleValueAggregate(SQLModel, table=True):
    vehicle_id: str = Field(primary_key=True)
    total_saved: float = 0.0
    total_risk: float = 0.0
    value_score: float = 0.0
