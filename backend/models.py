from sqlalchemy import Column, Integer, Float, String, DateTime
from database import Base

from datetime import datetime


class SensorReading(Base):

    __tablename__ = "sensor_readings"

    id = Column(Integer, primary_key=True, index=True)

    temperature = Column(Float)
    pressure = Column(Float)
    vibration = Column(Float)

    severity = Column(String)

    temp_zscore = Column(Float)
    pressure_zscore = Column(Float)
    vibration_zscore = Column(Float)

    timestamp = Column(DateTime, default=datetime.utcnow)