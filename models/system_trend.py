
from sqlmodel import SQLModel, Field
from datetime import datetime
import uuid

class SystemTrend(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    system: str
    occurrence_count: int = 0
    last_updated: datetime = Field(default_factory=datetime.utcnow)
