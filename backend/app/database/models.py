from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean
from sqlalchemy.sql import func
from backend.app.database.connection import Base

class Incident(Base):
    __tablename__ = "incidents"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    camera_id = Column(Integer, default=1)
    passenger_id = Column(Integer)
    train_state = Column(String(50))
    danger_duration = Column(Float)
    risk_level = Column(String(20))
    reason = Column(String(255))
    snapshot_path = Column(String(255), nullable=True)
    status = Column(String(20), default="OPEN")

class Alert(Base):
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    incident_id = Column(Integer, nullable=True)
    message = Column(String(255))
    level = Column(String(20))
