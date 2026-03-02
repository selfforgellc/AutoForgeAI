
from sqlmodel import SQLModel, Field
from datetime import datetime
import uuid

class ResolutionHistory(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    vehicle_id: str
    diagnosis_id: str
    previous_severity: str
    resolved_at: datetime = Field(default_factory=datetime.utcnow)
