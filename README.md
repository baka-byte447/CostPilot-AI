# CostPilot-AI
*Autonomous cloud cost optimization powered by reinforcement learning*

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-100%25-green.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-19-blue.svg)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-100%25-blue.svg)](https://www.typescriptlang.org/)
[![Docker](https://img.shields.io/badge/Docker-Enabled-blue.svg)](https://www.docker.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](http://makeapullrequest.com)

CostPilot-AI is an autonomous infrastructure scaling engine that optimizes cloud resources in real-time. By continuously analyzing live metrics and forecasting future workload demand, the system employs reinforcement learning to make intelligent scaling decisions. It ensures your infrastructure maintains high availability while dynamically eliminating idle capacity waste, providing complete transparency through an LLM-driven explanation pipeline. This tool is designed for DevOps and platform engineers seeking to automate cloud cost efficiency without sacrificing reliability.

## Demo

![Dashboard Preview](docs/assets/dashboard-preview.png)

* Live CPU and memory utilization charts pulled directly from Prometheus
* Reinforcement learning decision feed showing scaling actions and reward metrics
* Cloud cost forecasting projected alongside current operational expenses
* Real-time AWS connection and Auto Scaling Group status tracking
* Complete historical log of executed scaling actions and safety overrides

## Features

* **Live metrics collection**: Ingests CPU, memory, and network data every 10 seconds via psutil and Prometheus.
* **Reinforcement learning scaling**: Utilizes a Q-learning agent operating across a 3D state space for optimal resource allocation.
* **LLM decision explainer**: Generates plain English rationales using the Groq llama-3.1-8b-instant model, backed by a deterministic rule-based fallback.
* **Demand forecasting**: Predicts infrastructure load via Facebook Prophet with a moving-average baseline fallback.
* **AWS EC2 Auto Scaling integration**: Interacts directly with Auto Scaling Groups using the official boto3 SDK.
* **Kubernetes scaling support**: Native integration with the Python k8s client for container orchestration.
* **Safety engine**: Enforces strict replica clamping and guardrails across all automated scaling paths.
* **Real-time React dashboard**: Surfaces dynamic telemetry using Chart.js, Recharts, and Framer Motion.
* **Per-user data isolation**: Secures metrics and configurations via JWT authentication and user-scoped boundaries.
* **Persistent RL state**: Ensures continuous learning by persisting the Q-table to disk across application restarts.

## System architecture

```text
[Prometheus / psutil]
       |
       v
[Metrics Collector] ---> [SQLite: metrics.db]
       |
       v
[Prophet Forecaster] (fallback: moving-average)
       |
       v
[Q-Learning RL Agent] <--- [q_table.json]
       |
       v
[Safety Engine] ---> [AWS EC2 Auto Scaling / Kubernetes]
       |
       v
[Groq LLM Explainer] ---> [audit_log table]
       
[React Dashboard] <--- reads from all layers via FastAPI
```

Module mapping:
* [Metrics Collector]: collector.py
* [Prophet Forecaster]: forecasting_model.py
* [Q-Learning RL Agent]: agent.py + environment.py
* [Safety Engine]: safety_engine.py + aws_scaling_executor.py
* [Groq LLM Explainer]: explainer.py
* [React Dashboard]: Overview.tsx

## Getting started

### Prerequisites
* Python 3.11+
* Node.js 18+
* Docker + docker-compose
* AWS account with IAM credentials (note: use IAM roles in production, never hardcode keys)
* Groq API key — get one free at console.groq.com

### Quick start with Docker (recommended)

```bash
git clone https://github.com/yourusername/CostPilot-AI.git
cd CostPilot-AI
cp .env.example .env
# Edit .env and fill in required values (see table below)
docker-compose up --build
```

* Backend runs at: http://localhost:8000
* Dashboard runs at: http://localhost:5173
* API docs at: http://localhost:8000/docs

### Manual setup (without Docker)

Backend:
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Frontend:
```bash
cd dashboard
npm install
npm run dev
```

### Environment variables

| Variable | Required | Default | Description |
|---|---|---|---|
| JWT_SECRET | yes | none | Secret key for signing JWTs. Must be set or app will not start. |
| AWS_ACCESS_KEY_ID | no | none | AWS key. Use IAM roles in production. |
| AWS_SECRET_ACCESS_KEY | no | none | AWS secret. Use IAM roles in production. |
| AWS_REGION | yes | us-east-1 | AWS region for EC2/Auto Scaling calls |
| GROQ_API_KEY | yes | none | Groq API key for LLM explanations |
| CORS_ORIGINS | no | http://localhost:5173 | Allowed frontend origins |
| PROMETHEUS_URL | no | http://localhost:9090 | Prometheus server URL |
| AUTH_REQUIRED | no | false | Set to true in production |

### Verify it is running

```bash
curl http://localhost:8000/api/health
# Expected: {"status": "ok", ...}

python backend/scripts/validate_startup.py
# Checks JWT, AWS config, DB schema, Prometheus, RL agent

python backend/scripts/smoke_test.py
# Hits all endpoints and prints pass/fail for each
```

## Project structure

```text
CostPilot-AI/
├── .env / .env.example / .env.local
├── docker-compose.yml
├── howtorun.md / setupmodule.md
├── backend/
│   ├── requirements.txt
│   ├── scripts/
│   │   ├── validate_startup.py      # checks JWT, AWS keys, DB schema on boot
│   │   └── smoke_test.py            # hits all endpoints and asserts responses
│   └── app/
│       ├── main.py                  # FastAPI entrypoint, CORS, middleware
│       ├── api/                     # routers: auth, aws, cost, forecast, metrics, optimize, rl
│       ├── auth/                    # JWT validation, security utilities
│       ├── aws/                     # boto3 wrappers: cost_explorer, ec2_controller, mock
│       ├── config/                  # Pydantic settings, SQLAlchemy engine
│       ├── k8s/                     # Kubernetes scaling logic
│       ├── ml/                      # Prophet forecasting, data loaders
│       ├── models/                  # SQLAlchemy models: metrics, user, aws_connection
│       ├── optimizer/               # scaling hub, AWS executor, safety engine, LLM explainer
│       ├── rl/                      # agent.py, environment.py, trainer.py
│       ├── services/                # metrics_service (core business logic)
│       ├── telemetry/               # Prometheus collector (collector.py)
│       └── workers/                 # background metric ingestion threads
├── dashboard/
│   ├── package.json
│   ├── tailwind.config.js
│   ├── vite.config.ts
│   └── src/
│       ├── App.tsx                  # routing entry point
│       ├── components/              # reusable UI: buttons, charts, cards
│       ├── layout/                  # Sidebar, app shell
│       ├── lib/                     # helpers, chart gradient utilities
│       ├── pages/                   # Overview.tsx, ConnectAWS.tsx
│       └── services/                # Axios API service definitions
├── database/
│   ├── init.sql                     # schema: metrics, costs, audit_log, aws_connections tables
│   └── metrics.db                   # SQLite physical file
└── rl_models/
    └── q_table.json                 # persistent Q-table for the RL agent
```

## How it works

1. Metrics collection
workers/metrics_collector.py runs a background thread every 10 seconds. collector.py uses psutil for CPU, memory, and network. When Prometheus is available it scrapes node_exporter too. Falls back to simulated realistic values if Prometheus is unreachable, with a 60s re-check TTL.

2. Data storage
All metrics are persisted to SQLite via SQLAlchemy (metrics.db). The schema (init.sql) includes: metrics, costs, audit_log, and aws_connections tables. Queries are scoped by user_id from the JWT token. Retention window: last 24 hours, max 100 rows per query.

3. Demand forecasting
ml/forecasting_model.py uses Prophet as the primary forecaster. If Prophet is unavailable or fewer than 20 data points exist, it falls back to a moving-average with linear drift. All predictions are clamped to [0, 100] for CPU/memory and [0, ∞) for cost.

4. RL agent
rl/agent.py implements Q-learning with a 3D state space: cpu_bucket (0-9) × memory_bucket (0-9) × request_bucket (0-9) = 1000 states. Actions: scale_down (0), maintain (1), scale_up (2). Reward: slo_bonus (2.0 if cpu ≤ 80%) − cost − penalty. Q-table persists to rl_models/q_table.json between restarts. Learning rate α=0.1, discount γ=0.85, exploration ε=0.1.

5. Scaling execution
optimizer/aws_scaling_executor.py calls the EC2 Auto Scaling API via boto3. k8s/ handles Kubernetes deployments. safety_engine.py clamps all decisions to [min_replicas, max_replicas] and enforces a max_scale_step per cycle. explainer.py generates a plain-English rationale via Groq LLM (rule-based fallback if API is unavailable). Every decision is written to the audit_log table.

## API reference

Auth:

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | /api/auth/login | no | Get JWT token |
| POST | /api/auth/register | no | Register new user |

Metrics:

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | /api/metrics | yes | Get recent metrics (last 24h, max 100) |
| GET | /api/health | no | System health check |

Forecast:

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | /api/forecast/system | yes | CPU/memory/request forecast (next 6 steps) |
| GET | /api/cost/forecast | yes | Cost forecast based on current scaling |

Optimization:

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | /api/optimize | yes | Trigger RL scaling decision |
| GET | /api/optimize/history | yes | Scaling action history |

AWS:

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | /api/aws/scale | yes | Direct scaling call (bypasses RL) |
| GET | /api/aws/status | yes | Current ASG desired/min/max capacity |
| POST | /api/aws/connect | yes | Save AWS connection credentials |

RL:

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | /api/rl/state | yes | Current Q-table stats and last action |
| POST | /api/rl/train | yes | Trigger a manual training cycle |

## Configuration

RL Agent parameters:

| Parameter | Default | Location | Description |
|---|---|---|---|
| alpha (learning rate) | 0.1 | rl/agent.py | How fast the agent updates Q-values |
| gamma (discount) | 0.85 | rl/agent.py | Weight given to future rewards |
| epsilon (exploration) | 0.1 | rl/agent.py | Probability of random action |
| min_replicas | 1 | optimizer/ | Safety floor for scaling down |
| max_replicas | 8 | optimizer/ | Safety ceiling for scaling up |
| max_scale_step | 4 | optimizer/ | Max replica change per decision |

Forecasting parameters:

| Parameter | Default | Description |
|---|---|---|
| lookback_window | 6 | Number of past data points used in moving-average |
| min_data_points | 20 | Minimum rows before Prophet is used |
| forecast_periods | 6 | Number of future steps to predict |
| fallback_trigger | Prophet unavailable | Triggers when model is absent or < min_data_points |

## Deployment

Production on AWS:
* Use IAM roles attached to your EC2 instance instead of access keys in .env
* Recommended instance: t3.medium for backend, t3.small for dashboard
* Set AUTH_REQUIRED=true
* Set CORS_ORIGINS to your actual domain
* Set JWT_SECRET to a randomly generated 64-character string:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```
* Switch SQLite to PostgreSQL for production (update DATABASE_URL in config)

Docker production:
```bash
docker-compose -f docker-compose.yml up -d --build
```
Use AWS Secrets Manager or SSM Parameter Store instead of .env in production.

Prometheus setup:
* Point PROMETHEUS_URL at your Prometheus instance
* node_exporter should run on each monitored instance (port 9100)
* Backend scrape interval: 10s for app metrics, 15s for node_exporter

## Contributing

Fork → branch → commit → PR

Branch naming:
* feat/your-feature
* fix/issue-description
* docs/what-you-updated

Before submitting a PR:
```bash
python backend/scripts/smoke_test.py
python backend/scripts/validate_startup.py
```

Both scripts must pass with no failures. See CONTRIBUTING.md for full guidelines.

## Known limitations

* SQLite is not recommended for production at scale — migrate to PostgreSQL using DATABASE_URL
* Q-table resets if rl_models/q_table.json is deleted — back it up after training
* Groq API has rate limits on the free tier — rule-based fallback activates automatically
* Dashboard timezone rendering depends on browser locale — timestamps are stored UTC and displayed in local time
* Only 12 of 1000 possible RL states may be visited early on — performance improves with runtime

## Roadmap

| Done | In Progress | Planned |
|---|---|---|
| Live metrics collection | Multi-user auth with full isolation | Multi-cloud support (GCP, Azure) |
| Q-learning RL agent | Audit log persistence across restarts | Grafana dashboard integration |
| LLM decision explainer | Bellman TD-learning fix (gamma term) | Slack / PagerDuty alerts on scaling events |
| AWS EC2 Auto Scaling integration | Dashboard UTC timezone alignment | Cost anomaly detection |
| Kubernetes support | | PostgreSQL migration path |
| React dashboard | | GitHub Actions CI pipeline |
| Prophet forecasting | | Q-table visualization in dashboard |
| Safety engine | | |
| JWT authentication | | |
| Docker compose setup | | |
| Startup validator | | |
| Smoke test suite | | |

## License

MIT License. Copyright (c) 2025 CostPilot-AI Contributors.

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

## Acknowledgements

* FastAPI — async-first, auto-generates OpenAPI docs, minimal boilerplate
* Prophet — handles seasonality and missing data better than ARIMA for infrastructure workloads
* Groq — fastest inference API available for real-time decision explanation
* psutil — cross-platform system metrics with zero infrastructure dependency
* Prometheus — industry standard for time-series metrics scraping
* React + Vite — fast HMR, TypeScript-first, ideal for real-time dashboards
* Shadcn + Radix UI — accessible, unstyled components that work with Tailwind
* boto3 — official AWS SDK, full EC2 Auto Scaling API support
