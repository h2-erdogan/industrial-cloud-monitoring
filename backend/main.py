from fastapi import FastAPI
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import engine, SessionLocal
from models import Base, SensorReading

from detector import RollingConfig, RollingStatsDetector


app = FastAPI()

# Create database tables
Base.metadata.create_all(bind=engine)


# -----------------------------
# Detector setup
# -----------------------------

cfg = RollingConfig(
    window_size=60,
    warn_z=2.0,
    alert_z=3.0
)

temp_detector = RollingStatsDetector(cfg)
press_detector = RollingStatsDetector(cfg)
vib_detector = RollingStatsDetector(cfg)


# -----------------------------
# Root endpoint
# -----------------------------

@app.get("/")
def root():
    return {
        "message": "Industrial Monitoring API Running"
    }


# -----------------------------
# Sensor schema
# -----------------------------

class SensorData(BaseModel):
    temperature: float
    pressure: float
    vibration: float


# -----------------------------
# Store sensor data
# -----------------------------

@app.post("/sensor-data")
def create_sensor_data(data: SensorData):

    db: Session = SessionLocal()

    # classify BEFORE update
    temp_status, temp_z = temp_detector.classify(data.temperature)
    press_status, press_z = press_detector.classify(data.pressure)
    vib_status, vib_z = vib_detector.classify(data.vibration)

    # update detector windows
    temp_detector.update(data.temperature)
    press_detector.update(data.pressure)
    vib_detector.update(data.vibration)

    # overall severity
    severity = "OK"

    statuses = [temp_status, press_status, vib_status]

    if "WARN" in statuses:
        severity = "WARN"

    if "ALERT" in statuses:
        severity = "ALERT"

    sensor_entry = SensorReading(
    temperature=data.temperature,
    pressure=data.pressure,
    vibration=data.vibration,

    severity=severity,

    temp_zscore=temp_z,
    pressure_zscore=press_z,
    vibration_zscore=vib_z
)

    db.add(sensor_entry)
    db.commit()
    db.refresh(sensor_entry)

    db.close()

    return {
        "message": "Sensor data stored successfully",
        "severity": severity,
        "z_scores": {
            "temperature": round(temp_z, 2),
            "pressure": round(press_z, 2),
            "vibration": round(vib_z, 2)
        }
    }


# -----------------------------
# Read sensor data
# -----------------------------

@app.get("/sensor-data")
def get_sensor_data():

    db: Session = SessionLocal()

    sensor_data = db.query(SensorReading).all()

    db.close()

    return sensor_data