
from sqlmodel import SQLModel, Field
import uuid

class Fleet(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    name: str

class FleetVehicle(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    fleet_id: str
    vehicle_id: str
