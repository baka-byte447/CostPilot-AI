# CostPilot-AI

CostPilot-AI is an intelligent cloud cost optimization and infrastructure monitoring system. It collects live infrastructure metrics, forecasts workload demand, estimates cloud costs, and uses a Reinforcement Learning (RL) agent to make autonomous scaling decisions — all surfaced through a real-time React dashboard.

---

## System Overview

CostPilot-AI is built around five integrated layers:

1. **Monitoring Layer** — Prometheus + Node Exporter scrape live system metrics every 5 seconds.
2. **Data Layer** — Metrics are stored in SQLite via SQLAlchemy, loaded for ML training and API queries.
3. **Prediction Layer** — Prophet-based time-series forecasting of CPU, memory, and request load.
4. **Optimization Layer** — A Q-learning RL agent determines scaling actions (scale up / maintain / scale down).
5. **Execution Layer** — Scaling decisions are applied to mock AWS (LocalStack) and real Azure resources, governed by a Safety Engine and explained by an LLM (Groq/LLaMA 3).

---

## Architecture

```
┌──────────────────────────────────────────────────────────┐
│                     React Dashboard (Vite + TS)          │
│  Overview · Live Infra · AI Optimizer · Intelligence      │
│  Governance · Explainability · Resource Inventory        │
└────────────────────────┬─────────────────────────────────┘
                         │ REST API
┌────────────────────────▼─────────────────────────────────┐
│                  FastAPI Backend                          │
│                                                          │
│  /metrics   /forecast   /cost   /optimize                │
│  /rl/decision/latest    /rl/stats                        │
│  /rl/aws/state          /rl/explanation/latest           │
│  /aws/*     /azure/*    /cloud_cost                      │
└──────┬──────────────┬──────────────────┬─────────────────┘
       │              │                  │
┌──────▼──────┐  ┌────▼─────┐  ┌────────▼────────┐
│  Prometheus │  │ SQLite   │  │ ML Forecasting  │
│  Node Exp.  │  │ metrics.db│  │ (Prophet)       │
└─────────────┘  └──────────┘  └────────┬────────┘
                                         │
                              ┌──────────▼──────────┐
                              │  RL Agent (Q-Learning)│
                              │  3D State Space       │
                              │  CPU × Memory × Reqs  │
                              └──────────┬────────────┘
                                         │
                    ┌────────────────────┼────────────────────┐
                    │                    │                     │
          ┌─────────▼──────┐  ┌──────────▼──────┐  ┌─────────▼──────┐
          │  Safety Engine  │  │  AWS Executor   │  │ Azure Executor  │
          │  (SLO + cooldown│  │  (LocalStack     │  │ (VMSS / ACI)   │
          │   guardrails)   │  │  ASG/ECS/EKS)   │  │                │
          └─────────┬───────┘  └─────────────────┘  └────────────────┘
                    │
          ┌─────────▼───────┐
          │  LLM Explainer  │
          │  Groq / LLaMA 3 │
          │  (rule fallback) │
          └─────────────────┘
```

---

## Features Implemented

### 🖥️ React Dashboard (Vite + TypeScript + Tailwind)

A fully functional, dark-mode glassmorphism dashboard with 7 pages:

| Page | Description |
|---|---|
| **Command Center (Overview)** | Live KPI cards (Azure cost, CPU, memory, RL decision, forecast cost), real-time CPU/memory chart from Prometheus, AI explanation panel, AWS resource table |
| **Live Infrastructure** | Real-time infrastructure health view |
| **AI Optimizer** | RL agent deep-dive — current decision, Q-value bar chart, state buckets (CPU/Mem/Req), scaling history timeline |
| **Intelligence** | Forecasting and ML insights |
| **Governance** | SLO compliance and policy controls |
| **Explainability** | Full RL decision trace with LLM/rule-based explanation, safety overrides, Q-value diff |
| **Resource Inventory** | AWS and Azure resource browser |

Dashboard auto-refreshes every 15 seconds and supports a manual "Execute Optimization" trigger.

---

### 📡 Metrics Collection

- Prometheus integration scraping at 5-second intervals
- Node Exporter for system-level metrics (CPU, memory, network)
- Background worker (`metrics_collector.py`) periodically fetching and storing metrics
- SQLite storage via SQLAlchemy ORM

---

### 🔌 FastAPI Backend

All modules are exposed as versioned REST endpoints:

| Module | Endpoints |
|---|---|
| Metrics | `GET /metrics` |
| Forecasting | `GET /forecast` |
| Cost | `GET /cost`, `GET /cloud_cost` |
| RL Optimizer | `GET /rl/decision/latest`, `GET /rl/stats`, `GET /rl/explanation/latest` |
| AWS | `GET /rl/aws/state`, `GET /aws/actions`, `GET /aws/costs` |
| Azure | `GET /azure/cost`, `GET /azure/vmss`, `GET /azure/aci` |
| Optimize trigger | `POST /optimize` |

Custom Prometheus metrics exposed at `/app_metrics` (request counts via middleware).

---

### 🤖 ML Forecasting (LSTM + Prophet)

Time-series forecasting of infrastructure metrics:
- **CPU usage**
- **Memory usage**
- **Request load**

**Primary model — NumPy LSTM**: A pure NumPy single-layer LSTM with full BPTT (backpropagation through time) and gradient clipping. Trains once and persists weights to `rl_models/lstm_<metric>.npz`; subsequent calls load the saved model for instant inference. Autoregressively forecasts 6 steps ahead (30-minute horizon at 5-minute resolution).

**Fallback — Facebook Prophet**: Used as a cold-start fallback when fewer than 21 data rows exist. Automatically selected by the dispatcher.

**Auto-dispatch logic**:
- `>= 21 rows` → LSTM
- `< 21 rows` → Prophet
- LSTM failure → Prophet fallback with log warning

Forecast feeds both the cost predictor and dashboard KPI widgets. The `model_used` and `rows_used` fields are included in all forecast responses.

---

### 💸 Cost Estimation

- **Azure**: Monthly spend tracking via `azure-mgmt-costmanagement`, remaining credit calculation
- **AWS**: Cost Explorer integration via `boto3`
- **Forecast cost**: Predicted hourly cost derived from ML-forecasted resource usage

---

### 🧠 Reinforcement Learning Optimizer

A custom Q-learning agent trained to determine optimal scaling policies:

| Component | Detail |
|---|---|
| **State space** | 3D discretized space: CPU bucket × Memory bucket × Request bucket → 1,000 states |
| **Actions** | `scale_up`, `maintain`, `scale_down` |
| **Reward function** | Penalizes over/under-provisioning and SLO violations |
| **Q-Table** | Persisted to `rl_models/q_table.npy` |
| **Epsilon-greedy** | Exploration decays over training episodes |

**Feedback Loop (fixed)**: The environment now correctly simulates the post-action state transition:
- `reset()` preserves `current_replicas` across cycles (no longer resets to 2 each tick)
- `env.step()` calls `_simulate_next_state()` — `scale_up` reduces CPU/memory load proportionally to the new replica ratio; `scale_down` raises them
- The trainer stores `_last_next_state` from `step()` and uses it as the Bellman next-state in `agent.update()`, giving the agent real transition signal rather than the raw next Prometheus poll

Key files:
- `backend/app/rl/agent.py` — Q-learning agent
- `backend/app/rl/environment.py` — RL environment with reward shaping and state simulation
- `backend/app/rl/trainer.py` — Training loop + live decision inference with corrected feedback loop

---

### 🔒 Data Integrity & Metric Sanitization

Negative CPU values from Prometheus corrupted RL training states and LSTM training data. A three-layer sanitization pipeline was added:

| Layer | Location | Action |
|---|---|---|
| **Ingestion clamp** | `metrics_service.py` | `_clamp()` applied before DB write — CPU/memory clamped to `[0, 100]`, request_load to `[0, ∞)`. Logs a warning when clamping fires |
| **Read-time clamp** | `data_loader.py` | Clamped again on DB read before passing to LSTM/Prophet |
| **Agent guard** | `agent.py → get_state_index()` | `max(0.0, ...)` applied to all inputs before bucketing — prevents negative Q-table indices |
| **One-shot cleanup** | `utils/cleanup_db.py` | Zeroed **77 existing corrupt rows** in `metrics.db` on first run |

The root cause: `rate(node_cpu_seconds_total{mode="idle"}[1m])` returns `NaN` or `>1.0` on Node Exporter cold-start, causing the CPU query to produce negative values. Clamping at ingestion prevents this from ever reaching the DB again.

**Ops endpoints added:**
- `GET /forecast/db/cleanup` — re-runs the cleanup script via API
- `POST /forecast/lstm/retrain` — forces LSTM weight retrain from latest DB data

---

### 🛡️ Safety Engine (SLO Guardrails)

The Safety Engine sits between the RL agent's proposed action and actual execution. It validates against configurable SLO thresholds and enforces cooldowns.

Configurable via environment variables:

| Parameter | Default | Env |
|---|---|---|
| Max CPU % | 85 | `SLO_MAX_CPU` |
| Max Memory % | 90 | `SLO_MAX_MEMORY` |
| Max Request Load | 2.0 | `SLO_MAX_REQUESTS` |
| Min Replicas | 1 | `SLO_MIN_REPLICAS` |
| Max Replicas | 8 | `SLO_MAX_REPLICAS` |
| Max Scale Step | 2 | `SLO_MAX_SCALE_STEP` |
| Cooldown (seconds) | 30 | `SLO_COOLDOWN_SECONDS` |

If a proposed action violates any rule, the engine overrides it to a safe action and logs the violation. The override is surfaced in the Explainability dashboard.

---

### 💬 LLM Explainability (Groq / LLaMA 3)

Every scaling decision is explained in plain English:

- **Primary**: Groq API (`llama3-8b-8192`) generates a 2–3 sentence reasoning in under 8 seconds
- **Fallback**: Rule-based explainer covers all action types (scale_up, scale_down, maintain, safety-override) when Groq is unavailable
- **Output includes**: action taken, CPU/Memory/Request context, replica count, estimated hourly cost, safety override reason (if any)

---

### ☁️ AWS Integration (LocalStack Mock)

Full mock AWS environment running via LocalStack for local development:

| Service | Implementation |
|---|---|
| **ASG** | Mock Auto Scaling Groups with desired/min/max capacity |
| **ECS** | Mock ECS clusters and services with task counts |
| **EKS** | Mock EKS node groups |
| **Cost Explorer** | Mock cost data via `boto3` |
| **Action Log** | Recent scaling actions tracked in-memory and exposed via API |

AWS is seeded automatically via `seed_localstack.py` on startup.

---

### 🔷 Azure Integration

Real Azure SDK integration (or configurable mock):

| Service | SDK |
|---|---|
| **VMSS** | `azure-mgmt-compute` — scale VM Scale Sets |
| **ACI** | `azure-mgmt-containerinstance` — scale container groups |
| **Cost** | `azure-mgmt-costmanagement` — monthly spend tracking |
| **Monitor** | `azure-mgmt-monitor` — metric ingestion |

Azure mode is toggled via `AZURE_MODE` environment variable.

---

## Project Structure

```
CostPilot-AI/
│
├── backend/
│   ├── app/
│   │   ├── api/               # FastAPI route handlers (metrics, forecast, cost, rl, aws, azure)
│   │   ├── aws/               # AWS client, EC2/ECS/EKS controllers, mock_aws, seed_localstack
│   │   ├── azure/             # Azure client, VMSS/ACI/cost controllers
│   │   ├── cloud/             # Abstract cloud compute/cost interfaces
│   │   ├── config/            # DB session and app config
│   │   ├── cost/              # Cost estimation logic
│   │   ├── k8s/               # Kubernetes scaling controller
│   │   ├── ml/                # Prophet forecasting model + data loader
│   │   ├── models/            # SQLAlchemy DB models
│   │   ├── optimizer/         # Safety engine, explainer, AWS/Azure scaling executors
│   │   ├── rl/                # RL agent, environment, trainer
│   │   ├── services/          # Prometheus query helpers
│   │   ├── utils/             # Shared utilities
│   │   ├── workers/           # Background metric collector
│   │   └── main.py            # FastAPI app entry point
│   ├── Dockerfile
│   └── requirements.txt
│
├── dashboard/                 # React + Vite + TypeScript frontend
│   └── src/
│       ├── pages/             # Overview, LiveInfra, Intelligence, AIOptimizer,
│       │                      # Governance, Explainability, Resources
│       ├── components/        # AWSStatePanel, AzurePanel, RLPanel, SafetyPanel,
│       │                      # ExplainPanel, CostPanel, MetricsChart, ForecastChart
│       ├── layout/            # MainLayout (sidebar + topbar)
│       ├── services/          # api.ts — typed API client
│       └── lib/               # chartUtils
│
├── monitoring/
│   └── prometheus/            # prometheus.yml (scrape config)
│
├── database/
│   └── metrics.db             # SQLite metrics storage
│
├── rl_models/
│   └── q_table.npy            # Persisted Q-table
│
├── docker-compose.yml         # Prometheus + Node Exporter + LocalStack + Backend
├── .env                       # API keys and cloud credentials
└── README.md
```

---

## Running the System

### Prerequisites

- Docker & Docker Compose
- Python 3.10+ (for local backend dev)
- Node.js 18+ (for dashboard dev)

---

### Run with Docker

```bash
docker-compose up --build
```

Services started:

| Service | Port |
|---|---|
| FastAPI Backend | `8000` |
| Prometheus | `9090` |
| Node Exporter | `9100` |
| LocalStack (AWS) | `4566` |

---

### Run Dashboard (dev)

```bash
cd dashboard
npm install
npm run dev
```

Dashboard available at `http://localhost:5173`

---

### Environment Variables (`.env`)

| Variable | Purpose |
|---|---|
| `GROQ_API_KEY` | LLM explainability via Groq (optional, falls back to rule-based) |
| `AWS_MODE` | `true` to use LocalStack mock AWS |
| `AWS_ENDPOINT_URL` | LocalStack URL (`http://localstack:4566`) |
| `AZURE_MODE` | `true` to enable Azure SDK integrations |
| `AZURE_LOCATION` | Azure region |
| `AZURE_RESOURCE_GROUP` | Azure RG for VMSS/ACI |
| `SLO_MAX_CPU` | CPU threshold for scale-down safety (default: 85) |
| `SLO_MAX_MEMORY` | Memory threshold (default: 90) |
| `SLO_MAX_REPLICAS` | Upper replica cap (default: 8) |
| `SLO_COOLDOWN_SECONDS` | Minimum time between scaling actions (default: 30) |

---

## Technology Stack

| Category | Tools |
|---|---|
| **Backend** | FastAPI, Uvicorn, SQLAlchemy |
| **Monitoring** | Prometheus, Node Exporter, prometheus-client |
| **ML / Forecasting** | NumPy LSTM (BPTT), Facebook Prophet (fallback), Pandas |
| **Reinforcement Learning** | Custom Q-Learning (NumPy) with corrected feedback loop |
| **LLM Explainability** | Groq API (LLaMA 3-8B) + rule-based fallback |
| **Cloud — AWS** | boto3 + LocalStack (ASG, ECS, EKS, Cost Explorer) |
| **Cloud — Azure** | azure-mgmt-compute, azure-mgmt-containerinstance, azure-mgmt-costmanagement |
| **Database** | SQLite |
| **Frontend** | React 18, Vite, TypeScript, Tailwind CSS, Chart.js, Framer Motion |
| **Containerization** | Docker, Docker Compose |
| **Orchestration** | Kubernetes (optional) |

---

## Roadmap

- [x] LSTM forecasting model (pure NumPy, BPTT, auto-dispatch with Prophet fallback)
- [x] RL feedback loop — corrected state transition with environment simulation
- [x] Negative CPU data sanitization — clamp at ingestion, read-time, and agent layer
- [ ] Transformer-based forecasting (multi-head attention over LSTM)
- [ ] Grafana dashboards for historical metric exploration
- [ ] Distributed RL training with experience replay
- [ ] Anomaly detection with alerting
- [ ] Multi-cloud cost comparison and arbitrage
- [ ] Real-time WebSocket push for dashboard updates
- [ ] CI/CD pipeline integration

---

## License

This project is currently under development.
