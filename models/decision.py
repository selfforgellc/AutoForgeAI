
from sqlmodel import SQLModel, Field
from datetime import datetime
import uuid

class Decision(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    vehicle_id: str
    diagnosis_id: str
    decision_type: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
