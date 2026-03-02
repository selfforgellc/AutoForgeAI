
from sqlmodel import SQLModel, Field
from datetime import datetime
import uuid

class TimelineEvent(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    vehicle_id: str
    event_type: str
    reference_id: str | None = None
    payload: str | None = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
