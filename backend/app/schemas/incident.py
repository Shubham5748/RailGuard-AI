from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class IncidentBase(BaseModel):
    passenger_id: int
    train_state: str
    danger_duration: float
    risk_level: str
    reason: str
    camera_id: int = 1
    snapshot_path: Optional[str] = None
    status: str = "OPEN"

class IncidentCreate(IncidentBase):
    pass

class IncidentResponse(IncidentBase):
    id: int
    timestamp: datetime

    class Config:
        orm_mode = True

class AnalyticsResponse(BaseModel):
    total_incidents: int
    critical_alerts: int
    high_alerts: int
