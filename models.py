from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime
import uuid

class Vehicle(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    year: int
    make: str
    model: str
    trim: Optional[str] = None
    image_url: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Diagnosis(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    vehicle_id: str
    recommendation: str
    confidence: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class Decision(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    vehicle_id: str
    diagnosis_id: str
    decision: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
