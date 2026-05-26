# Industrial Cloud Monitoring System

![CI](https://github.com/h2-erdogan/industrial-cloud-monitoring/actions/workflows/ci.yml/badge.svg)

Real-time industrial sensor monitoring platform built with FastAPI, PostgreSQL, Docker, Grafana, and GitHub Actions CI/CD.

---

## Dashboard Preview

![Grafana Dashboard](assets/dashboard.png)

---

## Features

- Real-time industrial sensor simulation
- Rolling z-score anomaly detection
- FastAPI REST API backend
- PostgreSQL time-series data storage
- Grafana live monitoring dashboards
- Dockerized infrastructure
- GitHub Actions CI/CD pipeline
- Severity classification system (OK / WARN / ALERT)
- Real-time monitoring visualization

---

## Tech Stack

### Backend
- Python
- FastAPI
- SQLAlchemy

### Database
- PostgreSQL

### Monitoring
- Grafana

### DevOps
- Docker
- Docker Compose
- GitHub Actions CI/CD

---

## Architecture

```text
Sensor Simulator
        ↓
FastAPI Backend API
        ↓
Anomaly Detection Engine
        ↓
PostgreSQL Database
        ↓
Grafana Dashboards
```

---

## Project Structure

```text
industrial-cloud-monitoring/
│
├── backend/
│   ├── main.py
│   ├── database.py
│   ├── detector.py
│   ├── models.py
│   └── simulator.py
│
├── infra/
│   └── docker-compose.yml
│
├── .github/
│   └── workflows/
│       └── ci.yml
│
├── requirements.txt
├── README.md
└── .gitignore
```

---

## Run Project

### Clone repository

```bash
git clone https://github.com/h2-erdogan/industrial-cloud-monitoring.git
cd industrial-cloud-monitoring
```

---

### Start infrastructure

```bash
docker compose -f infra/docker-compose.yml up --build
```

This starts:

- PostgreSQL
- Grafana
- FastAPI backend

---

### Run sensor simulator

Open a new terminal:

```bash
python3 backend/simulator.py
```

The simulator continuously sends sensor data to the API.

---

## Grafana Dashboard

Grafana URL:

```text
http://localhost:3000
```

Default credentials:

```text
Username: admin
Password: admin123
```

---

## API Endpoints

### Create sensor data

```http
POST /sensor-data
```

### Retrieve sensor data

```http
GET /sensor-data
```

Swagger documentation:

```text
http://localhost:8001/docs
```

---

## Example Sensor Data

```json
{
  "temperature": 61.2,
  "pressure": 5.4,
  "vibration": 1.8
}
```

---

## CI/CD Pipeline

GitHub Actions pipeline automatically:

- Installs dependencies
- Builds Docker image
- Validates project structure
- Runs CI workflow on every push and pull request

Pipeline file:

```text
.github/workflows/ci.yml
```

---

## Key Highlights

- Real-time industrial monitoring system
- Fully containerized architecture
- Live Grafana dashboards
- CI/CD automation with GitHub Actions
- REST API with FastAPI
- PostgreSQL data persistence
- Real-time anomaly detection workflow

---

## Future Improvements

### Cloud & DevOps
- Kubernetes deployment
- AWS cloud deployment
- Terraform infrastructure provisioning
- Prometheus monitoring

### Streaming
- MQTT integration
- Kafka streaming

### AI / Analytics
- Machine learning anomaly detection
- Predictive maintenance models

---

## Author

Hasibe Erdogan

GitHub:
https://github.com/h2-erdogan