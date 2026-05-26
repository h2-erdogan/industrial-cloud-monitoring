# Industrial Cloud Monitoring System

Real-time industrial sensor monitoring platform built with FastAPI, PostgreSQL, Docker, and Grafana.

## Features

- Real-time sensor simulation
- Rolling z-score anomaly detection
- FastAPI backend API
- PostgreSQL time-series storage
- Grafana live dashboards
- Dockerized infrastructure
- Severity classification (OK / WARN / ALERT)

---

## Tech Stack

- Python
- FastAPI
- PostgreSQL
- SQLAlchemy
- Docker
- Grafana

---

## Architecture

Sensor Simulator
→ FastAPI API
→ Anomaly Detection Engine
→ PostgreSQL
→ Grafana Dashboards

---

## Run Project

### Start infrastructure

```bash
docker compose -f infra/docker-compose.yml up -d
```

### Run backend

```bash
cd backend
uvicorn main:app --reload --port 8001
```

### Run simulator

```bash
python backend/simulator.py
```

---

## Grafana

URL:

http://localhost:3000

Default credentials:

- admin
- admin123

---

## API Endpoints

### POST sensor data

```http
POST /sensor-data
```

### Get sensor data

```http
GET /sensor-data
```

---

## Future Improvements

- MQTT integration
- Kafka streaming
- Kubernetes deployment
- AWS cloud deployment
- Prometheus monitoring
- ML anomaly detection
