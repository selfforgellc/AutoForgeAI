
from sqlmodel import SQLModel, Field

class VehicleValueAggregate(SQLModel, table=True):
    vehicle_id: str = Field(primary_key=True)
    total_saved: float = 0.0
    total_risk: float = 0.0
    value_score: float = 0.0
