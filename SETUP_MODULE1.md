# Module 1: Telemetry Ingestion Setup Guide

This guide walks you through implementing and verifying Module 1: **Telemetry & Data Ingestion**.

## Overview

Module 1 collects raw telemetry data (CPU, memory, I/O, request load) and makes it persistent in a time-series database (Prometheus TSDB).

### What Gets Collected:
- ✅ System metrics (CPU, memory, disk, network)
- ✅ Application metrics (API requests, latency, errors)
- ✅ Infrastructure health (uptime, service status)
- ✅ Performance metrics (request sizes, response times)

### Architecture:
```
┌─────────────────┐
│   Backend App   │  Exposes metrics on port 8000/metrics
│   (FastAPI)     │
└────────┬────────┘
         │
         │ /metrics endpoint (Prometheus format)
         │
┌────────▼────────┐
│  Prometheus     │  Scrapes every 15 seconds
│  (Port 9090)    │  Stores in TSDB for 30 days
└────────┬────────┘
         │
         │ Time-series data
         │
┌────────▼────────┐
│  Grafana/QL     │  Query and visualize
│  (Port 3000)    │
└─────────────────┘
```

## Prerequisites

- Docker & Docker Compose installed
- Python 3.11+ (optional, for running tests locally)
- Git
- 2GB+ RAM available

## Step 1: Install Dependencies

### 1.1 Python Packages

```bash
cd backend
pip install -r requirements.txt
```

Key packages installed:
- `fastapi` - Web framework
- `uvicorn` - ASGI server
- `prometheus-client` - Metrics library
- `psutil` - System metrics
- `requests` - HTTP client

### 1.2 Verify Installation

```bash
python -c "import prometheus_client; print('✓ prometheus-client installed')"
python -c "import psutil; print('✓ psutil installed')"
python -c "import fastapi; print('✓ fastapi installed')"
```

## Step 2: Start the Monitoring Stack

### 2.1 Start Services with Docker Compose

```bash
cd monitoring
docker-compose up -d
```

### 2.2 Verify Services Started

```bash
docker-compose ps
```

Expected output:
```
NAME              COMMAND                    SERVICE         STATUS
prometheus        "/bin/prometheus..."       prometheus      Up 5 seconds
node_exporter     "/bin/node_exporter..."    node_exporter   Up 5 seconds
backend           "uvicorn app.main:app..."  backend         Up 5 seconds
grafana           "/run.sh"                  grafana         Up 5 seconds
```

### 2.3 Check Logs

If any service fails, check logs:

```bash
# Check backend logs
docker-compose logs backend -f

# Check Prometheus logs
docker-compose logs prometheus -f

# Check all logs
docker-compose logs -f
```

## Step 3: Verify Telemetry Collection

### 3.1 Check Backend Health

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "costpilot-backend",
  "version": "1.0.0"
}
```

### 3.2 Check System Metrics Endpoint

```bash
curl http://localhost:8000/api/system-metrics | python -m json.tool
```

Expected response:
```json
{
  "timestamp": "2024-03-03T10:30:45.123456",
  "hostname": "localhost",
  "cpu": {
    "usage_percent": 25.5,
    "count": 8,
    "per_cpu": [22.1, 28.3, ...]
  },
  "memory": {
    "used_bytes": 2147483648,
    "available_bytes": 6442450944,
    "total_bytes": 8589934592,
    "percent": 25.0
  },
  "disk": {...},
  "network": {...},
  "summary": {
    "app_name": "costpilot-backend",
    "uptime_seconds": 45.67
  }
}
```

### 3.3 Check Prometheus /metrics Endpoint

```bash
curl http://localhost:8000/metrics | head -20
```

Expected output (Prometheus text format):
```
# HELP system_cpu_usage_percent CPU usage percentage
# TYPE system_cpu_usage_percent gauge
system_cpu_usage_percent{host="localhost"} 25.5
# HELP system_memory_usage_bytes Memory usage in bytes
# TYPE system_memory_usage_bytes gauge
system_memory_usage_bytes{host="localhost",type="used"} 2.147483648e+09
system_memory_usage_bytes{host="localhost",type="available"} 6.442450944e+09
...
```

### 3.4 Verify Prometheus is Scraping

1. Open http://localhost:9090 in your browser
2. Go to **Status** → **Targets**
3. Verify all targets show **UP**:
   - prometheus
   - node_exporter
   - backend

Expected view:
```
Endpoint              Health  Labels
prometheus:9090      UP      job="prometheus"
node_exporter:9100   UP      job="node_exporter"
backend:8000         UP      job="backend"
```

### 3.5 Run Automated Verification

```bash
python scripts/fetch_metrics.py --all
```

This will:
- ✓ Check backend health
- ✓ Fetch system metrics
- ✓ Verify /metrics endpoint
- ✓ Query Prometheus TSDB
- ✓ Run stress test

Expected output:
```
[OK] Backend is healthy: healthy
[OK] System metrics retrieved successfully
[OK] Prometheus metrics retrieved successfully
[OK] Prometheus TSDB is running
[OK] Prometheus returned 5 sample metrics

[OK] Stress test complete: 10 successful, 0 failed

[OK] All checks passed! Telemetry is working correctly.
```

## Step 4: Verify Data Persistence

### 4.1 Run Test Queries in Prometheus

Open http://localhost:9090 and test these PromQL queries:

1. **Check if metrics exist**:
   ```promql
   up{job="backend"}
   ```
   Should return: `1` (up) or `0` (down)

2. **CPU usage**:
   ```promql
   system_cpu_usage_percent{job="backend"}
   ```
   Should show current CPU percentage

3. **Memory usage**:
   ```promql
   system_memory_percent{job="backend"}
   ```
   Should show memory usage %

4. **API requests**:
   ```promql
   increase(api_requests_total[5m])
   ```
   Should show API request volume

5. **Uptime**:
   ```promql
   application_uptime_seconds
   ```
   Should show seconds since backend started

### 4.2 Verify TSDB Persistence

Prometheus stores data in `monitoring/prometheus_data/`:

```bash
ls -lh monitoring/prometheus_data/
```

Should show:
```
wal/          # Write-ahead log
01HMRHQ0V0FQJ59J3XWJF8PK3D/  # Block directories
```

Each block represents a 2-hour chunk of data.

### 4.3 Stop and Restart Services

Test that data persists:

```bash
# Stop services
cd monitoring
docker-compose down

# Verify data directory still exists
ls -lh prometheus_data/

# Restart services
docker-compose up -d

# Check metrics still exist
curl http://localhost:9000/api/v1/query?query=up
```

The data should still be there! ✓

## Step 5: Set Up Grafana Dashboards (Optional)

### 5.1 Access Grafana

1. Open http://localhost:3000
2. Login: `admin` / `admin`
3. Click "Go to home" if prompted to change password

### 5.2 Add Prometheus Data Source

1. Click ⚙️ (Settings) → Data Sources
2. Click "Add data source"
3. Select "Prometheus"
4. Set URL: `http://prometheus:9090`
5. Click "Save & Test" → Should show "Data source is working"

### 5.3 Create a Simple Dashboard

1. Click **+** (Create) → Dashboard → New Panel
2. In the query section:
   - Select data source: Prometheus
   - Query: `system_cpu_usage_percent{job="backend"}`
3. Set Title: "CPU Usage"
4. Click "Apply"
5. Click "Save" and name the dashboard "CostPilot Overview"

Example dashboard queries:
```promql
# CPU Usage
system_cpu_usage_percent

# Memory Usage %
system_memory_percent

# API Requests/sec
rate(api_requests_total[1m])

# Request Latency (P95)
histogram_quantile(0.95, rate(api_request_duration_seconds_bucket[5m]))
```

## Troubleshooting

### Issue: Backend won't start

```bash
docker-compose logs backend
```

**Solution**: Ensure port 8000 is not already in use:
```bash
netstat -an | grep 8000
# Kill the process if needed
```

### Issue: Prometheus targets are DOWN

```bash
curl http://localhost:9090/api/v1/targets
```

**Solution**: 
1. Check docker network: `docker network ls`
2. Verify backend is running: `docker-compose ps`
3. Check backend logs: `docker-compose logs backend`

### Issue: No metrics in Prometheus

Wait at least 30 seconds (2 scrape cycles), then:

```bash
# Generate some traffic
curl http://localhost:8000/health

# Wait 15-30 seconds

# Check metrics
curl 'http://localhost:9090/api/v1/query?query=api_requests_total'
```

### Issue: High memory usage

Reduce retention time in `docker-compose.yml`:
```yaml
command:
  - '--storage.tsdb.retention.time=7d'  # Changed from 30d
```

Then restart: `docker-compose up -d`

## Success Criteria

✅ **Module 1 is complete when**:

1. Backend API responds to `/health` requests
2. Backend exposes metrics on `/metrics` endpoint
3. Prometheus scrapes backend metrics every 15 seconds
4. Prometheus shows all targets as UP
5. PromQL queries return non-empty results
6. Data persists across container restarts
7. `scripts/fetch_metrics.py --all` passes all checks
8. You can see metrics in Prometheus UI at http://localhost:9090

## Key Metrics Being Collected

| Metric | Type | Purpose |
|--------|------|---------|
| `system_cpu_usage_percent` | Gauge | CPU utilization |
| `system_memory_percent` | Gauge | Memory utilization |
| `system_disk_usage_bytes` | Gauge | Disk space usage |
| `system_network_bytes_sent_total` | Counter | Network outbound traffic |
| `system_network_bytes_received_total` | Counter | Network inbound traffic |
| `api_requests_total` | Counter | Total API requests |
| `api_request_duration_seconds` | Histogram | Request latency distribution |
| `application_uptime_seconds` | Gauge | Backend uptime |
| `telemetry_scrapes_total` | Counter | Telemetry collection cycles |

## Next Module Preview

Once Module 1 is verified, the next step is **Module 2: Data Storage & Preprocessing**:
- Store metrics in InfluxDB or PostgreSQL
- Clean and normalize data
- Compute sliding-window features
- Create aggregated views

## References

- Prometheus: http://localhost:9090
- Backend: http://localhost:8000
- Grafana: http://localhost:3000
- [Prometheus Docs](https://prometheus.io/docs/)
- [PromQL Guide](https://prometheus.io/docs/prometheus/latest/querying/basics/)

---

**Status**: ✓ Module 1 - Telemetry Ingestion ✅ READY

Next: Module 2 - Data Storage & Preprocessing
