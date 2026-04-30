# 🚀 CostPilot-AI — How to Run

> Complete list of commands to set up and run every part of the project.

---

## 📋 Prerequisites

Make sure the following are installed on your machine:

| Tool       | Version   | Check Command         |
| ---------- | --------- | --------------------- |
| Python     | 3.11+     | `python --version`    |
| Node.js    | 18+       | `node --version`      |
| npm        | 9+        | `npm --version`       |
| Docker     | 24+ *(optional)* | `docker --version` |
| Git        | any       | `git --version`       |

---

## 1️⃣ Clone the Repository

```bash
git clone https://github.com/<your-username>/CostPilot-AI.git
cd CostPilot-AI
```

---

## 2️⃣ Environment Configuration

```bash
# Copy the example env file and fill in your values
cp .env.example .env
```

Open `.env` and configure:

```env
# Backend
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000

# Prometheus (only needed for Docker setup)
PROMETHEUS_URL=http://localhost:9090

# AWS (optional – for cloud integration)
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret

# Azure (optional)
AZURE_SUBSCRIPTION_ID=your_subscription_id
AZURE_CLIENT_ID=your_client_id
AZURE_CLIENT_SECRET=your_secret
```

---

## 3️⃣ Backend (FastAPI) — Port `8000`

### Create a virtual environment

```bash
# Create venv
python -m venv .venv

# Activate — Windows (PowerShell)
.\.venv\Scripts\Activate.ps1

# Activate — Windows (CMD)
.\.venv\Scripts\activate.bat

# Activate — macOS / Linux
source .venv/bin/activate
```

### Install dependencies

```bash
pip install -r backend/requirements.txt
```

### Run the backend server

```bash
# Option 1: Using uvicorn directly
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload

# Option 2: Run from the backend directory
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Verify the backend is running

```bash
# Health check
curl http://localhost:8000/health

# API docs (open in browser)
# http://localhost:8000/docs
```

---

## 4️⃣ Dashboard (React + Vite) — Port `4000`

```bash
# Navigate to the dashboard directory
cd dashboard

# Install dependencies
npm install

# Start the development server
npm run dev
```

The dashboard will be available at **http://localhost:4000**

### Other dashboard commands

```bash
# Build for production
npm run build

# Preview the production build
npm run preview

# Lint the code
npm run lint
```

---

## 5️⃣ Frontend (Static HTML) — Any Port

The frontend is a static HTML file. You can serve it with any static server:

```bash
# Option 1: Using Python's built-in server
cd frontend
python -m http.server 5500

# Option 2: Using VS Code Live Server extension
# Right-click index.html → "Open with Live Server"
```

The frontend will be available at **http://localhost:5500**

---

## 6️⃣ Docker Setup (All Services)

### Start all services

```bash
# Start everything (backend, Prometheus, Grafana, Node Exporter)
docker-compose up -d

# Start and rebuild images
docker-compose up -d --build
```

### Service ports (Docker)

| Service        | Port   | URL                         |
| -------------- | ------ | --------------------------- |
| Backend API    | `8000` | http://localhost:8000       |
| Prometheus     | `9090` | http://localhost:9090       |
| Grafana        | `3000` | http://localhost:3000       |
| Node Exporter  | `9100` | http://localhost:9100       |

> **Grafana default login:** `admin` / `admin`

### Docker management commands

```bash
# View running containers
docker-compose ps

# View logs (all services)
docker-compose logs -f

# View logs (specific service)
docker-compose logs -f backend

# Stop all services
docker-compose down

# Stop and remove volumes
docker-compose down -v

# Rebuild a specific service
docker-compose build backend
```

---

## 7️⃣ Running Everything Together (Local Dev)

Open **3 separate terminals** and run:

### Terminal 1 — Backend

```bash
cd "c:\E\mini project sem 4\CostPilot-AI"
.\.venv\Scripts\Activate.ps1
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Terminal 2 — Dashboard

```bash
cd "c:\E\mini project sem 4\CostPilot-AI\dashboard"
npm run dev
```

### Terminal 3 — Frontend (optional)

```bash
cd "c:\E\mini project sem 4\CostPilot-AI\frontend"
python -m http.server 5500
```

---

## 🔗 Quick Reference — All URLs

| Service          | URL                                  |
| ---------------- | ------------------------------------ |
| Backend API      | http://localhost:8000                |
| Backend Docs     | http://localhost:8000/docs           |
| Backend ReDoc    | http://localhost:8000/redoc          |
| Health Check     | http://localhost:8000/health         |
| Dashboard        | http://localhost:4000                |
| Frontend         | http://localhost:5500                |
| Prometheus       | http://localhost:9090 *(Docker only)*|
| Grafana          | http://localhost:3000 *(Docker only)*|

---

## 🛠️ Troubleshooting

### Port already in use

```bash
# Find the process using a specific port (Windows)
netstat -ano | findstr :8000

# Kill the process by PID
taskkill /PID <PID> /F
```

### Virtual environment issues

```bash
# Delete and recreate
Remove-Item -Recurse -Force .venv
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend/requirements.txt
```

### Node modules issues

```bash
# Delete and reinstall
cd dashboard
Remove-Item -Recurse -Force node_modules
npm install
```

### Docker issues

```bash
# Reset everything
docker-compose down -v
docker system prune -f
docker-compose up -d --build
```
