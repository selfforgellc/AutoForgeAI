from __future__ import annotations

from sqlmodel import SQLModel, Field
from datetime import datetime
import uuid


class IssueStatus(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)

    vehicle_id: str
    diagnosis_id: str
    severity: str = "5"

    resolved: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)

    resolved_at: datetime | None = None
    resolved_reason: str | None = None