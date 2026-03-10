# CostPilot-AI

CostPilot-AI is an intelligent cloud cost optimization and monitoring system designed to collect infrastructure metrics, forecast workload demand, estimate infrastructure cost, and dynamically optimize Kubernetes scaling decisions.

The system integrates monitoring, machine learning forecasting, and reinforcement learning-based optimization to automatically analyze system load and recommend or apply scaling actions for Kubernetes deployments.

---

# System Overview

CostPilot-AI consists of four major components:

1. **Monitoring Layer**

   * Prometheus collects infrastructure metrics.
   * Node Exporter exposes system-level metrics.
   * FastAPI backend exposes application metrics.

2. **Data Processing Layer**

   * Metrics are periodically collected from Prometheus.
   * Data is stored in a local SQLite database.

3. **Prediction Layer**

   * Time-series forecasting models predict future resource usage.
   * Prophet and ML models forecast CPU, memory, and request load.

4. **Optimization Layer**

   * Reinforcement learning agents determine optimal scaling decisions.
   * Kubernetes controller applies scaling to deployments.

---

# Architecture

```
                 +----------------------+
                 |     Node Exporter    |
                 |   System Metrics     |
                 +----------+-----------+
                            |
                            v
                     +-------------+
                     | Prometheus  |
                     | Metrics DB  |
                     +------+------+
                            |
                            v
                    +---------------+
                    | FastAPI Backend|
                    | Metrics APIs   |
                    +-------+--------+
                            |
           +----------------+----------------+
           |                                 |
           v                                 v
   Forecasting Models                 RL Optimizer
  (Prophet / ML Models)            (Scaling Decision)
           |                                 |
           +---------------+-----------------+
                           |
                           v
                    Kubernetes Controller
                 (Deployment Auto Scaling)
```

---

# Features Implemented

### Metrics Collection

* Prometheus integration for infrastructure monitoring
* Node Exporter for system metrics
* Background worker to periodically collect metrics
* Storage of metrics in SQLite database

### API Layer (FastAPI)

Available API modules:

* Metrics API
* Forecasting API
* Cost estimation API
* Optimization API

### Prometheus Integration

* Custom metrics exposed via `/app_metrics`
* Request counting middleware using `prometheus-client`

### Machine Learning Forecasting

Time series forecasting of:

* CPU usage
* Memory usage
* Request load

Implemented using:

* Facebook Prophet
* Scikit-Learn models

### Cost Forecasting

Infrastructure cost prediction based on predicted resource usage.

### Reinforcement Learning Optimizer

A Q-learning based RL agent is implemented to determine scaling policies.

Components include:

* RL Environment
* RL Agent
* Model training pipeline
* Q-table persistence

### Kubernetes Control

The system can dynamically scale Kubernetes deployments using the Kubernetes Python client.

Example action:

```
scale_deployment("load-test-app", "default", replicas=5)
```

### Load Testing Deployment

A sample Kubernetes deployment (`load-test-app.yaml`) is provided for testing scaling behavior.

---

# Project Structure

```
CostPilot-AI
│
├── backend
│   ├── app
│   │   ├── api                # API endpoints
│   │   ├── config             # DB and application configuration
│   │   ├── cost               # Cost prediction models
│   │   ├── k8s                # Kubernetes controller logic
│   │   ├── ml                 # Forecasting models and data loaders
│   │   ├── models             # Database models
│   │   ├── optimizer          # Scaling decision logic
│   │   ├── rl                 # Reinforcement learning agent
│   │   ├── services           # Business logic layer
│   │   ├── utils              # Utility modules
│   │   └── workers            # Background metric collectors
│   │
│   ├── Dockerfile
│   └── requirements.txt
│
├── monitoring
│   ├── prometheus             # Prometheus configuration
│   └── node_exporter
│
├── database
│   └── metrics.db             # SQLite metrics storage
│
├── rl_models
│   └── q_table.npy            # RL model persistence
│
├── docker-compose.yml
└── README.md
```

---

# Running the System

## Prerequisites

* Docker
* Docker Compose
* Python 3.10+
* Kubernetes cluster (optional for scaling features)

---

## Run with Docker

Start the monitoring stack and backend service:

```
docker-compose up --build
```

Services started:

| Service         | Port |
| --------------- | ---- |
| FastAPI Backend | 8000 |
| Prometheus      | 9090 |
| Node Exporter   | 9100 |

---

## Access Services

Backend API

```
http://localhost:8000
```

Prometheus Dashboard

```
http://localhost:9090
```

Node Exporter Metrics

```
http://localhost:9100/metrics
```

---

# Prometheus Metrics

The backend exposes application metrics at:

```
/app_metrics
```

Metrics include:

* HTTP request counts
* Application metrics for monitoring

Prometheus scrapes this endpoint every **5 seconds**.

---

# Kubernetes Scaling

CostPilot-AI can scale Kubernetes deployments programmatically.

Example:

```
scale_deployment("load-test-app", "default", replicas=3)
```

The system interacts with the Kubernetes API using the Python Kubernetes client.

---

# Machine Learning Components

### Forecasting Models

Predict future resource usage using:

* Prophet
* Scikit-Learn

Forecasted metrics:

* CPU usage
* Memory usage
* Request load

### Reinforcement Learning

The RL module learns optimal scaling policies based on system state.

Components include:

* Environment simulation
* Q-learning agent
* Policy training
* Q-table persistence

---

# Future Work

Planned improvements include:

* Automatic horizontal pod autoscaling based on RL decisions
* Advanced cost optimization strategies
* Real-time anomaly detection
* Distributed training for RL models
* Multi-cloud cost estimation support
* Grafana dashboards for visualization

---

# Technology Stack

| Category         | Tools                     |
| ---------------- | ------------------------- |
| Backend          | FastAPI                   |
| Monitoring       | Prometheus, Node Exporter |
| ML               | Prophet, Scikit-Learn     |
| Database         | SQLite, SQLAlchemy        |
| Containerization | Docker                    |
| Orchestration    | Kubernetes                |
| Optimization     | Reinforcement Learning    |

---

# License

This project is currently under development.



