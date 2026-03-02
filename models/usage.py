
from sqlmodel import SQLModel, Field
from datetime import datetime
import uuid

class Usage(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    user_id: str
    date: str  # YYYY-MM-DD
    diagnosis_count: int = 0
