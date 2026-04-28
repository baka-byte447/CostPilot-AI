# CostPilot-AI

CostPilot-AI is an intelligent cloud cost optimization and infrastructure monitoring system. It collects live infrastructure metrics from Azure VMSS, forecasts workload demand, estimates cloud costs, and uses a Reinforcement Learning (RL) agent to make autonomous scaling decisions — all surfaced through a real-time React dashboard.

---

### ✨ Major Enhancements
- **🔷 Real Azure VMSS Integration**: Live metrics collection from Azure Monitor (CPU, Network In/Out)
- **🛡️ Advanced Validation System**: RBAC checking with detailed permission guidance
- **📊 Enhanced Status Tracking**: Real-time cloud resource health monitoring with degradation handling
- **🎨 Streamlined UI**: Removed unnecessary components, focused on Azure VMSS monitoring
- **🤖 Fixed AI Reasoning**: Updated Groq API integration with `llama-3.1-8b-instant` model
- **⏰ Time Zone Fixes**: Resolved dashboard chart time drift issues
- **🔐 Improved Security**: Better credential handling with error resilience


---

## System Overview

CostPilot-AI is built around five integrated layers:

1. **Monitoring Layer** — Azure Monitor integration for live VMSS metrics every 30 seconds
2. **Data Layer** — Metrics stored in SQLite via SQLAlchemy with per-user isolation
3. **Prediction Layer** — NumPy LSTM forecasting with Prophet fallback for CPU, memory, and request load
4. **Optimization Layer** — Q-learning RL agent determines scaling actions (scale up / maintain / scale down)
5. **Execution Layer** — Scaling decisions applied to Azure VMSS, governed by Safety Engine and explained by LLM

---

## Architecture

```
┌──────────────────────────────────────────────────────────┐
│                     React Dashboard (Vite + TS)          │
│  Overview · Service · AI Optimizer · Cloud Setup         │
└────────────────────────┬─────────────────────────────────┘
                         │ REST API
┌────────────────────────▼─────────────────────────────────┐
│                  FastAPI Backend                          │
│                                                          │
│  /metrics   /forecast   /cost   /optimize                │
│  /rl/decision/latest    /rl/stats                        │
│  /rl/explanation/latest   /credentials/*                 │
│  /azure/*    /auth/*     /cloud_cost                     │
└──────┬──────────────┬──────────────────┬─────────────────┘
       │              │                  │
┌──────▼──────┐  ┌────▼─────┐  ┌────────▼────────┐
│  Azure      │  │ SQLite   │  │ ML Forecasting  │
│  Monitor    │  │ metrics.db│  │ (LSTM/Prophet) │
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
          │  Safety Engine  │  │  Azure Executor │  │  LLM Explainer │
          │  (SLO + cooldown│  │  (VMSS Scaling) │  │  Groq API      │
          │   guardrails)   │  │                 │  │  Rule fallback│
          └─────────────────┘  └─────────────────┘  └────────────────┘
```

---

---

## 🎯 Features Implemented

### 🖥️ React Dashboard (Vite + TypeScript + Tailwind)

A streamlined, dark-mode glassmorphism dashboard with 4 core pages:

| Page | Description |
|---|---|
| **Overview** | Live KPI cards (Azure cost, CPU, memory, RL decision), real-time Azure Monitor metrics chart, AI explanation panel |
| **Service** | Azure VMSS details, status monitoring, cost tracking, latest captured signals |
| **AI Optimizer** | RL agent deep-dive — current decision, Q-value chart, state buckets, live reasoning |
| **Cloud Setup** | Azure credential management, VMSS configuration, validation system |

Dashboard auto-refreshes every 15 seconds and shows real-time connection status.

---

### 🔐 User Authentication & Cloud Credential Management

**Multi-tenant secure system with per-user isolation:**
- **JWT Authentication**: Secure user registration and login
- **Encrypted Credentials**: Azure Service Principal credentials encrypted at rest
- **Validation System**: Automatic RBAC checking and permission guidance
- **Status Tracking**: Real-time monitoring of cloud connection health

---

### 📡 Real Azure Metrics Collection

**Live Azure Monitor integration:**
- **VMSS Metrics**: CPU percentage, Network In/Out totals
- **Smart Fallbacks**: Graceful degradation when Azure Monitor is unavailable
- **Error Resilience**: Continues operation even with partial credential failures
- **Status Dashboard**: Real-time health monitoring with detailed error messages

---

---

### � FastAPI Backend

All modules exposed as REST endpoints with comprehensive error handling:

| Module | Endpoints |
|---|---|
| Authentication | `POST /auth/register`, `POST /auth/login` |
| Credentials | `POST /credentials/azure`, `POST /credentials/azure/validate`, `GET /credentials/azure/status` |
| Metrics | `GET /metrics` (with metadata and status) |
| Forecasting | `GET /forecast` (LSTM + Prophet) |
| Cost | `GET /cost`, `GET /cloud_cost` |
| RL Optimizer | `GET /rl/decision/latest`, `GET /rl/stats`, `GET /rl/explanation/latest` |
| Azure | `GET /azure/cost/current-month`, `GET /azure/vmss` |
| Optimize trigger | `POST /optimize` |

---

### 🤖 ML Forecasting (NumPy LSTM + Prophet)

**Time-series forecasting of infrastructure metrics:**
- **CPU usage** - From Azure Monitor
- **Memory usage** - Note: Requires guest-level monitoring on VMSS
- **Request load** - Derived from Network In metrics

**Primary model — NumPy LSTM**: Pure NumPy implementation with BPTT and gradient clipping. Auto-saves weights for instant loading.

**Auto-dispatch logic**:
- `>= 21 rows` → LSTM
- `< 21 rows` → Prophet
- LSTM failure → Prophet fallback

---

### 🧠 Reinforcement Learning Optimizer

**Custom Q-learning agent for scaling decisions:**

| Component | Detail |
|---|---|
| **State space** | 3D discretized: CPU bucket × Memory bucket × Request bucket → 1,000 states |
| **Actions** | `scale_up`, `maintain`, `scale_down` |
| **Reward function** | Penalizes over/under-provisioning and SLO violations |
| **Q-Table** | Persisted to `rl_models/q_table.npy` |
| **Epsilon-greedy** | Exploration decays over training episodes |

---

### �️ Safety Engine (SLO Guardrails)

**Configurable safety constraints:**

| Parameter | Default | Environment Variable |
|---|---|---|
| Max CPU % | 85 | `SLO_MAX_CPU` |
| Max Memory % | 90 | `SLO_MAX_MEMORY` |
| Max Request Load | 2.0 | `SLO_MAX_REQUESTS` |
| Min Replicas | 1 | `SLO_MIN_REPLICAS` |
| Max Replicas | 8 | `SLO_MAX_REPLICAS` |
| Max Scale Step | 2 | `SLO_MAX_SCALE_STEP` |
| Cooldown (seconds) | 30 | `SLO_COOLDOWN_SECONDS` |

---

### 💬 LLM Explainability (Groq API)

**Every scaling decision explained in plain English:**
- **Primary**: Groq API (`llama-3.1-8b-instant`) generates 2-3 sentence reasoning
- **Fallback**: Rule-based explainer for all action types
- **Configurable**: Model selection via `GROQ_MODEL` environment variable

---

### 🔷 Azure Integration

**Real Azure SDK integration:**

| Service | SDK | Purpose |
|---|---|---|
| **VMSS** | `azure-mgmt-compute` | Scale VM Scale Sets |
| **Monitor** | `azure-mgmt-monitor` | Collect metrics via Azure Monitor |
| **Cost** | `azure-mgmt-costmanagement` | Monthly spend tracking |
| **Identity** | `azure-identity` | Service Principal authentication |

---

---

## 📋 Complete User Onboarding Guide

### 🎯 Prerequisites

**Required Accounts & Tools:**
1. **Azure Subscription** with owner or contributor access
2. **Azure CLI** installed locally
3. **Docker & Docker Compose** for running the application
4. **Git** for cloning the repository

### 🚀 Step 1: Azure VMSS Setup

**1.1. Login to Azure:**
```bash
az login
```

**1.2. Set your subscription:**
```bash
# List available subscriptions
az account list --output table

# Set your active subscription
az account set --subscription "YOUR_SUBSCRIPTION_ID"
```

**1.3. Create Resource Group:**
```bash
az group create \
  --name "costpilot-rg" \
  --location "eastus"
```

**1.4. Create Virtual Network:**
```bash
az network vnet create \
  --resource-group "costpilot-rg" \
  --name "costpilot-vnet" \
  --address-prefix "10.0.0.0/16" \
  --subnet-name "costpilot-subnet" \
  --subnet-prefix "10.0.1.0/24"
```

**1.5. Create Network Security Group:**
```bash
az network nsg create \
  --resource-group "costpilot-rg" \
  --name "costpilot-nsg"
```

**1.6. Create VM Scale Set:**
```bash
az vmss create \
  --resource-group "costpilot-rg" \
  --name "costpilot-vmss" \
  --image "UbuntuLTS" \
  --vm-sku "Standard_B2s" \
  --subnet "costpilot-subnet" \
  --nsg "costpilot-nsg" \
  --admin-username "azureuser" \
  --generate-ssh-keys \
  --instance-count 2 \
  --upgrade-policy-mode "Automatic" \
  --load-balancer "costpilot-lb"
```

**1.7. Enable Monitoring on VMSS:**
```bash
# Enable boot diagnostics
az vmss update \
  --resource-group "costpilot-rg" \
  --name "costpilot-vmss" \
  --set "virtualMachineProfile.osProfile.secrets=[]"

# Enable monitoring (if you have Azure Monitor for VMs enabled)
az monitor diagnostic-settings create \
  --resource "/subscriptions/YOUR_SUBSCRIPTION_ID/resourceGroups/costpilot-rg/providers/Microsoft.Compute/virtualMachineScaleSets/costpilot-vmss" \
  --name "costpilot-monitoring" \
  --workspace "/subscriptions/YOUR_SUBSCRIPTION_ID/resourceGroups/YOUR_LOG_ANALYTICS_RG/providers/Microsoft.OperationalInsights/workspaces/YOUR_WORKSPACE" \
  --metrics "[{'category': 'AllMetrics', 'enabled': true}]"
```

### 🔐 Step 2: Create Azure Service Principal

**2.1. Create Service Principal with minimal permissions:**
```bash
# Create Service Principal
az ad sp create-for-rbac \
  --name "costpilot-sp" \
  --role "Reader" \
  --scopes "/subscriptions/YOUR_SUBSCRIPTION_ID/resourceGroups/costpilot-rg" \
  --json-auth
```

**2.2. Note the output - you'll need these values:**
```json
{
  "appId": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "displayName": "costpilot-sp",
  "password": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
  "tenant": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
}
```

**2.3. Add Monitoring Reader role:**
```bash
# Get the Service Principal object ID
SP_OBJECT_ID=$(az ad sp show --id "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx" --query "id" -o tsv)

# Add Monitoring Reader role
az role assignment create \
  --assignee-object-id "$SP_OBJECT_ID" \
  --role "Monitoring Reader" \
  --scope "/subscriptions/YOUR_SUBSCRIPTION_ID/resourceGroups/costpilot-rg"
```

### 🚀 Step 3: Deploy CostPilot-AI

**3.1. Clone the repository:**
```bash
git clone https://github.com/your-username/CostPilot-AI.git
cd CostPilot-AI
```

**3.2. Configure environment variables:**
```bash
# Copy the example environment file
cp .env.example .env

# Edit the .env file with your configuration
nano .env
```

**Add these values to your `.env` file:**
```env
# Groq API for AI explanations (optional but recommended)
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama-3.1-8b-instant

# Azure Configuration
AZURE_MODE=true
AZURE_LOCATION=eastus
AZURE_RESOURCE_GROUP=costpilot-rg
AZURE_VMSS_NAME=costpilot-vmss

# SLO Configuration
SLO_MAX_CPU=85
SLO_MAX_MEMORY=90
SLO_MAX_REQUESTS=2.0
SLO_MIN_REPLICAS=1
SLO_MAX_REPLICAS=8
SLO_MAX_SCALE_STEP=2
SLO_COOLDOWN_SECONDS=30

# Security (generate your own strong keys)
JWT_SECRET=your_jwt_secret_here_minimum_32_characters
ENCRYPTION_KEY=your_encryption_key_here_minimum_32_characters
```

**3.3. Start the application:**
```bash
docker-compose up --build
```

Wait for all services to start. You should see:
- FastAPI Backend: `http://localhost:8000`
- React Dashboard: `http://localhost:5173`
- Prometheus: `http://localhost:9090`

### 🎯 Step 4: User Registration & Cloud Setup

**4.1. Register a new user account:**
1. Open `http://localhost:5173` in your browser
2. Click "Get Started" → "Register"
3. Fill in your email and password
4. Click "Create Account"

**4.2. Configure Azure credentials:**
1. After registration, you'll be redirected to Cloud Setup
2. Fill in your Azure Service Principal details:
   - **Tenant ID**: From the Service Principal creation output
   - **Client ID**: The "appId" from the output
   - **Client Secret**: The "password" from the output
   - **Subscription ID**: Your Azure subscription ID
   - **Resource Group**: `costpilot-rg`
   - **VMSS Name**: `costpilot-vmss`
   - **Location**: `eastus` (or your chosen region)

**4.3. Validate Azure permissions:**
1. Click "Validate permissions (Retry)" button
2. The system will check:
   - VMSS existence and accessibility
   - Azure Monitor metrics availability
   - Required RBAC permissions
3. If validation passes, you'll see a green "ok" status
4. If it fails, follow the displayed guidance to fix permissions

### 📊 Step 5: Monitor Your VMSS

**5.1. View the Overview dashboard:**
- Navigate to "Overview" in the sidebar
- See real-time CPU and network metrics from your VMSS
- Monitor AI optimization decisions
- Track cost predictions

**5.2. Check Service details:**
- Go to "Service" page
- View VMSS configuration and health status
- Monitor latest captured signals
- Track monthly Azure costs

**5.3. AI Optimization:**
- Visit "AI Optimizer" to see:
  - Current RL agent decisions
  - Q-value analysis
  - State bucket distribution
  - LLM explanations for scaling actions

---

## 🛠️ Troubleshooting Guide

### Common Issues & Solutions

**Issue: "Validation failed - permissions error"**
```bash
# Solution: Ensure proper RBAC roles are assigned
az role assignment create \
  --assignee "YOUR_SERVICE_PRINCIPAL_APP_ID" \
  --role "Reader" \
  --scope "/subscriptions/YOUR_SUBSCRIPTION_ID/resourceGroups/costpilot-rg"

az role assignment create \
  --assignee "YOUR_SERVICE_PRINCIPAL_APP_ID" \
  --role "Monitoring Reader" \
  --scope "/subscriptions/YOUR_SUBSCRIPTION_ID/resourceGroups/costpilot-rg"
```

**Issue: "No metrics available"**
- Check that your VMSS is running and has instances
- Verify Azure Monitor is configured correctly
- Wait 5-10 minutes for metrics to become available

**Issue: "Groq API not working"**
```bash
# Update your .env file with current model
GROQ_MODEL=llama-3.1-8b-instant
# Restart the backend container
docker-compose restart backend
```

---

## 🏗️ Project Structure

```
CostPilot-AI/
│
├── backend/
│   ├── app/
│   │   ├── api/               # FastAPI route handlers
│   │   ├── azure/             # Azure client and controllers
│   │   ├── models/            # SQLAlchemy DB models
│   │   ├── optimizer/         # Safety engine, explainer
│   │   ├── rl/                # RL agent, environment, trainer
│   │   ├── ml/                # LSTM/Prophet forecasting
│   │   ├── workers/           # Background metrics collector
│   │   └── main.py            # FastAPI app entry point
│   ├── Dockerfile
│   └── requirements.txt
│
├── dashboard/                 # React + Vite + TypeScript
│   └── src/
│       ├── pages/             # Overview, Service, AI Optimizer, Cloud Setup
│       ├── components/        # UI components
│       ├── layout/            # MainLayout with topbar and sidebar
│       └── services/          # API client
│
├── monitoring/
│   └── prometheus/            # Prometheus configuration
│
├── database/
│   └── metrics.db             # SQLite database
│
├── rl_models/                 # Persisted ML models
│   ├── q_table.npy
│   └── lstm_*.npz
│
├── docker-compose.yml         # Development environment
├── docker-compose.prod.yml    # Production environment
└── .env                       # Environment configuration
```

---

---

## 🚀 Deployment Options

### Option 1: Local Development
```bash
docker-compose up --build
```

### Option 2: Production Deployment
```bash
docker-compose -f docker-compose.prod.yml up -d --build
```

### Option 3: Cloud Deployment

**Vercel (Frontend) + Railway/Render (Backend):**
1. **Frontend**: Connect `dashboard/` directory to Vercel
2. **Backend**: Deploy `backend/` directory to Railway/Render
3. **Database**: Use managed PostgreSQL
4. **Environment Variables**: Configure all required variables

**Required Environment Variables for Production:**
- `DATABASE_URL` (PostgreSQL connection string)
- `JWT_SECRET` (strong random string)
- `ENCRYPTION_KEY` (strong random string)
- `GROQ_API_KEY` (for AI explanations)
- Azure credentials (for cloud integration)

---

## 🛠️ Technology Stack

| Category | Tools |
|---|---|
| **Backend** | FastAPI, Uvicorn, SQLAlchemy |
| **Frontend** | React 18, Vite, TypeScript, Tailwind CSS, Chart.js |
| **Database** | SQLite (dev), PostgreSQL (prod) |
| **ML/AI** | NumPy LSTM, Facebook Prophet, Q-Learning, Groq API |
| **Cloud** | Azure SDK (Compute, Monitor, Cost Management) |
| **Monitoring** | Prometheus, Azure Monitor |
| **Containerization** | Docker, Docker Compose |

---

## 🗺️ Development Roadmap

### ✅ Completed
- [x] Multi-user authentication with JWT
- [x] Real Azure VMSS metrics integration
- [x] NumPy LSTM forecasting with Prophet fallback
- [x] Q-learning RL agent with safety guardrails
- [x] LLM-powered explanations (Groq)
- [x] Comprehensive validation and status tracking
- [x] Streamlined Azure-focused UI

### 🚧 In Progress
- [ ] Memory metrics from VMSS (requires guest-level monitoring)
- [ ] Historical metrics dashboard
- [ ] Multi-cloud support expansion

### 📋 Planned
- [ ] Transformer-based forecasting models
- [ ] Anomaly detection with alerting
- [ ] WebSocket real-time updates
- [ ] CI/CD pipeline integration
- [ ] Grafana dashboards integration

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## 🆘 Support

If you encounter any issues or have questions:

1. **Check the troubleshooting guide** above
2. **Review the logs**: `docker-compose logs backend`
3. **Validate your Azure setup** using the Cloud Setup page
4. **Create an issue** on GitHub with detailed error messages

---

**Built with ❤️ for cloud cost optimization and intelligent infrastructure management.**
