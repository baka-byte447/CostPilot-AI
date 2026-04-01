# CostPilot-AI

CostPilot-AI is an automated cloud cost optimization system. It monitors infrastructure metrics, forecasts usage demand, and dynamically optimizes scaling targets for Kubernetes deployments.

The system combines local monitoring with time-series forecasting and reinforcement learning to decide when and how to scale infrastructure resources appropriately.

## Architecture

- **Monitoring Layer**: Uses Prometheus and Node Exporter to gather system metrics (CPU, Memory) and application metrics (Requests).
- **Backend API**: A FastAPI backend processes the metrics, stores them, and provides endpoints.
- **Data Preprocessing**: Cleans and normalizes incoming telemetry data.
- **Forecasting Models**: Time-series models to predict resource utilization.
- **Optimization Engine**: Reinforcement learning agent that generates optimal scaling actions to enforce workload requirements.

## Quickstart (Docker Compose)

1) Prereqs: Docker Desktop (or Docker Engine) with Compose v2.

2) Copy environment template (optional—defaults work):
```bash
cp .env.example .env
```

3) Start the full stack (Prometheus, Node Exporter, backend, Grafana):
```bash
docker compose up -d
```

4) Verify the backend is healthy:
```bash
curl http://localhost:8000/health
```

5) Open the built-in dashboards:
- FastAPI docs: http://localhost:8000/docs
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000 (admin / admin)
- Minimal HTML dashboard: open frontend/index.html locally and point it to http://localhost:8000

Notes:
- The SQLite database lives in the mounted ./database directory; data persists across restarts.
- The RL model artifacts are mounted from ./rl_models.
- Kubernetes scaling calls require access to a kubeconfig on the host; otherwise those endpoints will fail gracefully.

## Local Development (without Docker)

```bash
cd backend
python -m venv .venv && source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Prometheus and Grafana are only brought up via Docker; for local-only dev, you can point `PROMETHEUS_URL` to a running instance or accept zeros from the mocked collectors.

## Infrastructure Control

CostPilot-AI interacts directly with the Kubernetes API to adjust deployment replicas dynamically. Sample load testing manifests are included in the repository.

## Project Structure

- `backend/` - FastAPI backend, ML models, and RL agent
- `monitoring/` - Prometheus and Grafana setup
- `database/` - SQLite database bindings
- `scripts/` - Test utilities
- `rl_models/` - Reinforcement learning model states
