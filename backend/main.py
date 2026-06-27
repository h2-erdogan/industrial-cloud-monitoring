from fastapi import FastAPI
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import engine, SessionLocal
from models import Base, SensorReading
from detector import RollingConfig, RollingStatsDetector


app = FastAPI(
    title="Industrial Monitoring API",
    description="Real-time industrial sensor monitoring API with anomaly detection.",
    version="1.0.0"
)

Base.metadata.create_all(bind=engine)


cfg = RollingConfig(
    window_size=60,
    warn_z=2.0,
    alert_z=3.0
)

temp_detector = RollingStatsDetector(cfg)
press_detector = RollingStatsDetector(cfg)
vib_detector = RollingStatsDetector(cfg)


class SensorData(BaseModel):
    temperature: float
    pressure: float
    vibration: float


@app.get("/")
def root():
    return {
        "message": "Industrial Monitoring API Running"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "industrial-monitoring-api"
    }


@app.post("/sensor-data")
def create_sensor_data(data: SensorData):
    db: Session = SessionLocal()

    try:
        temp_status, temp_z = temp_detector.classify(data.temperature)
        press_status, press_z = press_detector.classify(data.pressure)
        vib_status, vib_z = vib_detector.classify(data.vibration)

        temp_detector.update(data.temperature)
        press_detector.update(data.pressure)
        vib_detector.update(data.vibration)

        statuses = [temp_status, press_status, vib_status]

        severity = "OK"

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

        return {
            "message": "Sensor data stored successfully",
            "severity": severity,
            "z_scores": {
                "temperature": round(temp_z, 2),
                "pressure": round(press_z, 2),
                "vibration": round(vib_z, 2)
            }
        }

    finally:
        db.close()


@app.get("/sensor-data")
def get_sensor_data():
    db: Session = SessionLocal()

    try:
        sensor_data = db.query(SensorReading).all()
        return sensor_data

    finally:
        db.close()