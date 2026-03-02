
from sqlmodel import SQLModel, Field
from datetime import datetime
import uuid

class AuditLog(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    user_id: str | None = None
    action: str
    endpoint: str
    method: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
