# CostPilot-AI

CostPilot-AI is an automated cloud cost optimization system. It monitors infrastructure metrics, forecasts usage demand, and dynamically optimizes scaling targets for Kubernetes deployments.

The system combines local monitoring with time-series forecasting and reinforcement learning to decide when and how to scale infrastructure resources appropriately.

## Architecture

- **Monitoring Layer**: Uses Prometheus and Node Exporter to gather system metrics (CPU, Memory) and application metrics (Requests).
- **Backend API**: A FastAPI backend processes the metrics, stores them, and provides endpoints.
- **Data Preprocessing**: Cleans and normalizes incoming telemetry data.
- **Forecasting Models**: Time-series models to predict resource utilization.
- **Optimization Engine**: Reinforcement learning agent that generates optimal scaling actions to enforce workload requirements.

## Running Locally

1. **Install dependencies:**  
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. **Start the monitoring services:**  
   ```bash
   cd monitoring
   docker-compose up -d
   ```

3. **Run the backend:**  
   ```bash
   cd backend
   uvicorn app.main:app --reload
   ```

## Infrastructure Control

CostPilot-AI interacts directly with the Kubernetes API to adjust deployment replicas dynamically. Sample load testing manifests are included in the repository.

## Project Structure

- `backend/` - FastAPI backend, ML models, and RL agent
- `monitoring/` - Prometheus and Grafana setup
- `database/` - SQLite database bindings
- `scripts/` - Test utilities
- `rl_models/` - Reinforcement learning model states
