# CostPilot-AI: Automated Cloud Cost Intelligence & Optimization

A machine learning-driven FinOps platform that intelligently optimizes cloud infrastructure costs while maintaining service reliability and performance SLOs.

## 🎯 Project Overview

CostPilot-AI automates cloud cost optimization by:
1. **Collecting telemetry** from cloud services and infrastructure
2. **Forecasting** future resource demand using ML models
3. **Optimizing** resource allocation using Reinforcement Learning
4. **Enforcing** SLA/SLO constraints automatically
5. **Orchestrating** infrastructure changes safely and reliably
6. **Auditing** every decision with full transparency
7. **Explaining** decisions in human-readable terms
8. **Visualizing** metrics, forecasts, and actions on dashboards

### Key Benefits
- 💰 **30-50% cost reduction** through intelligent resource optimization
- 📈 **100% SLA compliance** with constraint enforcement
- 🤖 **Fully automated** scaling without manual intervention
- 📊 **Complete audit trail** for compliance and FinOps
- 🧠 **Explainable AI** decisions for stakeholder trust

## 📁 Project Structure

```
CostPilot-AI/
│
├── backend/                          # FastAPI application
│   ├── app/
│   │   ├── api/                     # REST API endpoints
│   │   ├── telemetry/               # ✅ MODULE 1: Metrics collection
│   │   │   ├── collector.py
│   │   │   └── __init__.py
│   │   │
│   │   ├── forecasting/             # 🔜 MODULE 2: Demand prediction
│   │   │   └── predictor.py
│   │   │
│   │   ├── decision_engine/         # 🔜 MODULE 3: RL optimization
│   │   │   └── rl_agent.py
│   │   │
│   │   ├── constraints/             # 🔜 MODULE 4: SLA enforcement
│   │   │   └── validator.py
│   │   │
│   │   ├── orchestration/           # 🔜 MODULE 5: Cloud actuation
│   │   │   └── executor.py
│   │   │
│   │   ├── audit/                   # 🔜 MODULE 6: Decision logging
│   │   │   └── logger.py
│   │   │
│   │   ├── explainability/          # 🔜 MODULE 7: XAI explanations
│   │   │   └── explainer.py
│   │   │
│   │   ├── config/                  # Configuration management
│   │   ├── models/                  # Database models
│   │   ├── services/                # Business logic
│   │   ├── utils/                   # Utilities and helpers
│   │   └── main.py                  # FastAPI application entry point
│   │
│   ├── requirements.txt              # Python dependencies
│   └── Dockerfile                    # Container configuration
│
├── monitoring/                       # Prometheus + Grafana stack
│   ├── docker-compose.yml            # Service orchestration
│   ├── prometheus/
│   │   └── prometheus.yml            # Prometheus configuration
│   ├── README.md                     # Monitoring setup guide
│   └── prometheus_data/              # Time-series database (persistent)
│
├── database/                         # Database schemas
│   └── init.sql                      # SQL initialization script
│
├── scripts/                          # Testing and utility scripts
│   └── fetch_metrics.py              # Telemetry verification script
│
├── frontend/                         # 🔜 Web dashboard (Phase 2)
│   └── README.md                     # Frontend roadmap
│
├── SETUP_MODULE1.md                  # ✅ Module 1 setup guide
├── .env.example                      # Environment variables template
├── .gitignore                        # Git configuration
├── README.md                         # This file
└── .deep-research-report.md          # Architecture documentation

```

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.11+
- Git
- 4GB+ RAM

### Step 1: Clone and Setup

```bash
# Clone the repository
git clone <repo-url>
cd CostPilot-AI

# Create .env file (optional)
cp .env.example .env
```

### Step 2: Start Services

```bash
cd monitoring
docker-compose up -d
```

### Step 3: Verify Installation

```bash
# Check services
docker-compose ps

# Check backend health
curl http://localhost:8000/health

# Run verification
python scripts/fetch_metrics.py --all
```

### Step 4: Access Services

| Service | URL | Purpose |
|---------|-----|---------|
| Backend API | http://localhost:8000 | REST API, docs at /docs |
| Prometheus | http://localhost:9090 | Metrics database & query UI |
| Grafana | http://localhost:3000 | Dashboards (admin/admin) |
| Health Check | http://localhost:8000/health | Backend health status |
| Metrics | http://localhost:8000/metrics | Prometheus format metrics |
| System Metrics | http://localhost:8000/api/system-metrics | JSON metrics |

## 📋 Modules (Implementation Sequence)

### ✅ Module 1: Telemetry & Data Ingestion [DONE]
**Status**: Ready for testing
**Goal**: Collect raw metrics (CPU, memory, I/O, costs) continuously

**What's Implemented**:
- FastAPI backend with metrics collection
- Prometheus TSDB for time-series storage
- System metrics via psutil and Node Exporter
- Application metrics from FastAPI
- Data persistence (30-day retention)

**Key Files**:
- `backend/app/telemetry/collector.py` - Metrics collection
- `backend/app/main.py` - FastAPI app with /metrics endpoint
- `monitoring/docker-compose.yml` - Services orchestration
- `monitoring/prometheus/prometheus.yml` - Prometheus config
- `scripts/fetch_metrics.py` - Verification script

**Setup Guide**: See [SETUP_MODULE1.md](SETUP_MODULE1.md)

**Success Criteria**:
- ✅ Backend exposed on port 8000
- ✅ Prometheus scraping metrics every 15s
- ✅ `/metrics` endpoint returns Prometheus format
- ✅ `/api/system-metrics` returns JSON metrics
- ✅ Data persists in Prometheus TSDB
- ✅ `fetch_metrics.py --all` passes all checks

---

### 🔜 Module 2: Data Storage & Preprocessing [TODO]
**Goal**: Store, clean, and normalize telemetry data

**Planned**:
- InfluxDB or PostgreSQL for long-term storage
- ETL pipeline for data cleaning
- Sliding-window feature computation
- Data validation and quality checks
- Aggregated metrics views

**Expected Timeline**: 2-3 days

---

### 🔜 Module 3: Demand Forecasting Engine [TODO]
**Goal**: Predict future resource demand using ML

**Planned**:
- Time-series ML models (LSTM, Prophet, ARIMA)
- Short-term (1-72 hour) demand forecasts
- Forecast accuracy metrics (MAPE, MSE)
- Multiple model ensemble
- Real-time prediction API

**Expected Timeline**: 3-4 days

---

### 🔜 Module 4: RL Optimization (Decision Engine) [TODO]
**Goal**: Compute optimal scaling decisions

**Planned**:
- RL environment implementation (simulated cloud)
- Agent training with Stable-Baselines3
- Reward function (cost vs. performance trade-off)
- Policy deployment and control

**Expected Timeline**: 4-5 days

---

### 🔜 Module 5: Safety & Constraint Enforcement [TODO]
**Goal**: Enforce SLA/SLO constraints

**Planned**:
- SLA/RTO/RPO rule engine
- Constraint validation middleware
- Automatic policy adjustments
- Cost budget enforcement

**Expected Timeline**: 2 days

---

### 🔜 Module 6: Cloud Orchestration [TODO]
**Goal**: Execute scaling actions in real infrastructure

**Planned**:
- AWS/Azure/GCP SDK integration
- Kubernetes API client
- Safe action execution with rollback
- Error handling and retry logic

**Expected Timeline**: 3-4 days

---

### 🔜 Module 7: Audit & Logging [TODO]
**Goal**: Immutable audit trail for compliance

**Planned**:
- Event log database
- Full decision context logging
- Compliance report generation
- Audit trail queries

**Expected Timeline**: 2 days

---

### 🔜 Module 8: Explainable AI (XAI) [TODO]
**Goal**: Explain decisions in human terms

**Planned**:
- Rule-based and LLM-based explanations
- Decision rationale generation
- Stakeholder-facing reports

**Expected Timeline**: 2-3 days

---

### 🔜 Module 9: Dashboard & Reporting [TODO]
**Goal**: Visualize metrics, forecasts, and actions

**Complete Dashboards**:
- **FinOps Dashboard**: Cost trends, savings, budgets
- **Operations Dashboard**: SLA compliance, uptime, incidents
- **Engineering Dashboard**: Performance, resource utilization
- **Audit Dashboard**: Decision history, compliance logs
- **Action Timeline**: All scaling decisions with rationale

**Tech Stack**: Grafana + custom React UI

**Expected Timeline**: 4-5 days

---

## 🔧 Technology Stack

### Backend
- **Framework**: FastAPI (async)
- **Server**: Uvicorn (ASGI)
- **Monitoring**: Prometheus client
- **System Metrics**: psutil
- **Validation**: Pydantic

### Data & Storage
- **Metrics TSDB**: Prometheus (30-day retention)
- **Database**: PostgreSQL or SQLite (future modules)
- **Time-Series**: InfluxDB (future expansion)

### ML/Analytics
- **Forecasting**: scikit-learn, statsmodels, Prophet
- **RL Framework**: Stable-Baselines3
- **Data Processing**: Pandas, NumPy

### Visualization
- **Metrics**: Prometheus/Grafana
- **Dashboards**: Grafana + custom React
- **UI**: React, D3.js/Chart.js

### Infrastructure
- **Containerization**: Docker & Docker Compose
- **Cloud**: AWS/Azure/GCP SDKs
- **Orchestration**: Kubernetes (future)

## 📊 Metrics Currently Collected

### System Metrics
- CPU usage (%, per-core)
- Memory (used, available, percent)
- Disk (used, free, percent per mount)
- Network (bytes sent/received per interface)
- System uptime

### Application Metrics
- API requests (count, by method/endpoint/status)
- Request latency (distribution, percentiles)
- Request/response sizes
- Error rates (4xx, 5xx)
- Application uptime

### Infrastructure Metrics
- Service health (up/down status)
- Container metrics (Docker)
- Pod metrics (Kubernetes)

## 🏃 Running the Application

### Start Services
```bash
cd monitoring
docker-compose up -d
```

### Stop Services
```bash
docker-compose down
```

### View Logs
```bash
docker-compose logs -f backend
docker-compose logs -f prometheus
docker-compose logs -f grafana
```

### Rebuild Images
```bash
docker-compose down
docker-compose up -d --build
```

## 🧪 Testing

### Run Verification Script
```bash
# Full verification
python scripts/fetch_metrics.py --all

# Check only backend
python scripts/fetch_metrics.py --check-backend

# Check only Prometheus
python scripts/fetch_metrics.py --check-prometheus

# Run stress test
python scripts/fetch_metrics.py --stress-test
```

### Test PromQL Queries
Open http://localhost:9090 and try:

```promql
# Service health
up{job="backend"}

# CPU usage
system_cpu_usage_percent

# API requests per minute
rate(api_requests_total[1m])

# Request latency P95
histogram_quantile(0.95, api_request_duration_seconds_bucket)
```

## 📈 PromQL Query Examples

```promql
# Current values
system_cpu_usage_percent{job="backend"}
system_memory_percent{job="backend"}

# Rate of change (requests/sec)
rate(api_requests_total[5m])

# Aggregations
avg(system_memory_percent) by (host)
sum(api_requests_total) by (endpoint)

# Percentiles
histogram_quantile(0.99, api_request_duration_seconds_bucket)
histogram_quantile(0.95, api_request_size_bytes_bucket)

# Thresholds
system_cpu_usage_percent{job="backend"} > 80
system_memory_percent{job="backend"} > 90
```

## 🐛 Troubleshooting

### Services Won't Start
```bash
# Check if ports are in use
netstat -an | grep "8000\|9090\|3000\|9100"

# Check logs
docker-compose logs

# Rebuild
docker-compose down -v
docker-compose up -d --build
```

### Prometheus Targets DOWN
1. Check `monitoring/prometheus/prometheus.yml` config
2. Ensure backend is running
3. Verify Docker network: `docker network ls`
4. Check network connectivity: `docker-compose exec prometheus ping backend`

### No Metrics in Prometheus
1. Wait 30+ seconds (2 scrape intervals)
2. Generate traffic: `curl http://localhost:8000/health`
3. Check: `curl http://localhost:8000/metrics | head -20`
4. Query Prometheus: `up` should return 1

### High Memory Usage
In `docker-compose.yml`, reduce retention:
```yaml
command:
  - '--storage.tsdb.retention.time=7d'  # was 30d
```

## 📚 Documentation

- **[Module 1 Setup Guide](SETUP_MODULE1.md)** - Complete telemetry setup
- **[Monitoring README](monitoring/README.md)** - Prometheus/Grafana guide
- **[Frontend README](frontend/README.md)** - Dashboard roadmap
- **[Deep Research Report](.deep-research-report.md)** - Full architecture details
- **[Prometheus Docs](https://prometheus.io/docs/)** - Official Prometheus documentation
- **[PromQL Guide](https://prometheus.io/docs/prometheus/latest/querying/basics/)** - Query language reference

## 🎓 Architecture Decisions

### Why Prometheus for TSDB?
- ✅ Pull-based model (targets expose /metrics)
- ✅ Built-in time-series compression
- ✅ PromQL - powerful query language
- ✅ Time-based retention management
- ✅ Horizontal scalability (federated)
- ✅ Grafana integration

### Why Prometheus Client Library?
- ✅ Zero-dependency metric collection
- ✅ Multiple metric types (Gauge, Counter, Histogram, Summary)
- ✅ Automatic text format serialization
- ✅ Thread-safe operations

### Why FastAPI?
- ✅ Modern async/await support
- ✅ Auto OpenAPI documentation
- ✅ Built-in input validation (Pydantic)
- ✅ High performance (near native speed)
- ✅ Easy integration with Prometheus

## 🔐 Security Considerations

- [ ] Add authentication to API endpoints
- [ ] Enable HTTPS/TLS for all services
- [ ] Secure Prometheus with authentication
- [ ] Encrypt database credentials
- [ ] Implement rate limiting
- [ ] Add request validation
- [ ] Sanitize logs and error messages
- [ ] Use network policies/firewalls

## 🚦 Development Workflow

1. **Start services**: `cd monitoring && docker-compose up -d`
2. **Make changes**: Edit code in `backend/app/`
3. **Test locally**: `python -m pytest tests/`
4. **Verify metrics**: `python scripts/fetch_metrics.py --all`
5. **Check dashboard**: Open http://localhost:3000
6. **Commit changes**: `git add . && git commit -m "..."`
7. **Push**: `git push origin main`

## 📅 Timeline

| Module | Status | Days | Target Date |
|--------|--------|------|------------|
| 1. Telemetry | ✅ Done | 2 | Mar 3 |
| 2. Storage | 🔜 Todo | 2-3 | Mar 5-6 |
| 3. Forecasting | 🔜 Todo | 3-4 | Mar 8-10 |
| 4. RL Engine | 🔜 Todo | 4-5 | Mar 12-15 |
| 5. Constraints | 🔜 Todo | 2 | Mar 15-17 |
| 6. Orchestration | 🔜 Todo | 3-4 | Mar 19-21 |
| 7. Audit | 🔜 Todo | 2 | Mar 22-23 |
| 8. XAI | 🔜 Todo | 2-3 | Mar 24-26 |
| 9. Dashboard | 🔜 Todo | 4-5 | Mar 28-31 |

**Total**: ~3-4 weeks for MVP

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines (if exists).

## 📄 License

[Add license information]

## 📞 Support

For issues and questions:
1. Check existing issues on GitHub
2. Review the [troubleshooting section](#-troubleshooting)
3. Consult documentation in respective module directories
4. Open a new GitHub issue with details

## 🎉 Success!

**Module 1 ✅ is complete!**

**Next Step**: Start Module 2 - Data Storage & Preprocessing

---

**Last Updated**: March 3, 2026  
**Version**: 1.0.0 (Module 1 Complete)  
**Status**: In Development
