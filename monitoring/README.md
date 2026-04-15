# CostPilot-AI Monitoring Setup

This directory contains the monitoring stack for CostPilot-AI using Prometheus, Node Exporter, and Grafana.

## Overview

The monitoring stack collects and visualizes:
- **System Metrics**: CPU, memory, disk, network (via Node Exporter)
- **Application Metrics**: API requests, response times, errors (via FastAPI)
- **Infrastructure Metrics**: Service health, uptime, performance

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    CostPilot-AI Services                    │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Backend    │  │ Node         │  │ Prometheus   │      │
│  │   (FastAPI)  │  │ Exporter     │  │ (TSDB)       │      │
│  │   :8000      │  │ :9100        │  │ :9090        │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│       |                    |                  |              │
│   /metrics              /metrics            /api/           │
│   /health           (system stats)       (queries)          │
│   /api/system-      (4xx response)                          │
│   metrics                                                   │
└─────────────────────────────────────────────────────────────┘
         |                                        |
         └────────────────────┬───────────────────┘
                              |
                    ┌─────────┴─────────┐
                    │   Prometheus:     │
                    │   Scrapes metrics │
                    │   every 15s       │
                    └───────────────────┘
                              |
                   ┌──────────┴──────────┐
                   |                     |
              ┌─────────┐          ┌─────────┐
              │ Grafana │          │ Queries │
              │ :3000   │          │ for BI  │
              └─────────┘          └─────────┘
```

## Quick Start

### 1. Start the Monitoring Stack

From the project root directory:

```bash
cd monitoring
docker-compose up -d
```

This will start:
- **Prometheus** on http://localhost:9090
- **Node Exporter** on http://localhost:9100
- **Backend** on http://localhost:8000
- **Grafana** on http://localhost:3000

### 2. Verify Services are Running

```bash
docker-compose ps
```

Expected output:
```
NAME                COMMAND                  SERVICE             STATUS
backend             "uvicorn app.main:app"   backend             Up
grafana             "/run.sh"                grafana             Up
node_exporter       "/bin/node_exporter"     node_exporter       Up
prometheus          "/bin/prometheus..."     prometheus          Up
```

### 3. Test Telemetry Collection

Run the verification script:

```bash
python scripts/fetch_metrics.py --all
```

This will:
- Check backend health
- Fetch system metrics
- Verify Prometheus metrics endpoint
- Query Prometheus TSDB
- Run a stress test to generate metrics

## Accessing Services

| Service | URL | Purpose |
|---------|-----|---------|
| **Prometheus** | http://localhost:9090 | View metrics, run PromQL queries |
| **Backend Health** | http://localhost:8000/health | Check backend status |
| **Backend Metrics (JSON)** | http://localhost:8000/api/system-metrics | System metrics in JSON |
| **Backend Metrics (Prometheus)** | http://localhost:8000/metrics | Metrics in Prometheus format |
| **Grafana** | http://localhost:3000 | Create dashboards (admin/admin) |
| **Node Exporter** | http://localhost:9100/metrics | Raw system metrics |

## Key Metrics

### System Metrics (collected by Node Exporter)
- `system_cpu_usage_percent` - CPU usage percentage
- `system_memory_percent` - Memory usage percentage
- `system_memory_usage_bytes` - Memory usage in bytes
- `system_disk_usage_bytes` - Disk usage by mount point
- `system_network_bytes_sent_total` - Network bytes sent
- `system_network_bytes_received_total` - Network bytes received

### Application Metrics (collected by Backend)
- `api_requests_total` - Total API requests by method, endpoint, status
- `api_request_duration_seconds` - Request duration distribution
- `api_request_size_bytes` - Request body size distribution
- `api_response_size_bytes` - Response body size distribution
- `application_uptime_seconds` - Backend uptime
- `telemetry_scrapes_total` - Total telemetry collection cycles

## Prometheus Configuration

The Prometheus configuration is in `prometheus/prometheus.yml`:

- **Global scrape interval**: 15 seconds
- **Retention period**: 30 days
- **Scrape targets**:
  - Prometheus itself (:9090)
  - Node Exporter (:9100)
  - Backend application (:8000/metrics)

## Grafana Setup

### First Time Login

1. Go to http://localhost:3000
2. Login with `admin` / `admin`
3. You'll be prompted to change the password

### Add Prometheus Data Source

1. Click on "Configuration" (gear icon)
2. Select "Data Sources"
3. Click "Add data source"
4. Choose "Prometheus"
5. Set URL to `http://prometheus:9090`
6. Click "Save & Test"

### Create a Dashboard

1. Click "+" (Create) -> Dashboard
2. Click "Add new panel"
3. In the query editor, select Prometheus as data source
4. Enter a PromQL query (e.g., `system_cpu_usage_percent`)
5. Click "Apply"
6. Customize the panel and save the dashboard

## PromQL Query Examples

```promql
# Current CPU usage
system_cpu_usage_percent{job="node_exporter"}

# Memory usage over last 5 minutes
system_memory_percent{job="node_exporter"}

# API requests per second
rate(api_requests_total[5m])

# P95 request latency
histogram_quantile(0.95, api_request_duration_seconds)

# Success rate (non-5xx responses)
sum(rate(api_requests_total{status!~"5.."}[5m])) / 
sum(rate(api_requests_total[5m]))
```

## Data Persistence

Prometheus stores metrics in the `prometheus_data` volume. This is persistent across container restarts:

- **Location**: `monitoring/prometheus_data/`
- **Retention**: 30 days (configurable in docker-compose.yml)
- **Storage**: ~200MB per day for typical traffic

Grafana also stores dashboards and settings in `grafana_data/`.

## Troubleshooting

### Prometheus targets showing DOWN

**Problem**: Targets are DOWN in Prometheus UI

**Solution**:
1. Check if services are running: `docker-compose ps`
2. Check logs: `docker-compose logs prometheus`
3. Verify network connectivity between containers
4. Check prometheus.yml for correct hostnames

### No metrics appearing

**Problem**: Metrics are not being collected

**Solution**:
1. Ensure Node Exporter is running and exposed
2. Check Prometheus scrape interval (default 15s)
3. Generate load: `curl http://localhost:8000/health`
4. Wait 30+ seconds and check Prometheus again

### Grafana can't connect to Prometheus

**Problem**: Data source test fails

**Solution**:
1. Ensure Prometheus is running
2. Use correct hostname: `prometheus` (not `localhost`)
3. Use correct port: `9090`
4. Check network: `docker-compose config`

### High memory usage

**Problem**: Prometheus using too much memory

**Solution**:
1. Reduce retention period in docker-compose.yml
2. Reduce scrape frequency
3. Use metric relabeling to drop unnecessary metrics

## Stopping the Stack

```bash
docker-compose down
```

To also remove stored data:

```bash
docker-compose down -v
```

## Next Steps

1. **Data Storage** - Set up InfluxDB or other TSDB for long-term storage
2. **Alerting** - Configure Alertmanager for alerts on anomalies
3. **Dashboarding** - Build comprehensive Grafana dashboards
4. **Cloud Integration** - Add AWS CloudWatch, Azure Monitor exporters
5. **Authentication** - Enable Prometheus and Grafana authentication

## References

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Prometheus Query Language](https://prometheus.io/docs/prometheus/latest/querying/basics/)
- [Node Exporter](https://github.com/prometheus/node_exporter)
- [Grafana Documentation](https://grafana.com/docs/grafana/latest/)
- [Docker Compose Reference](https://docs.docker.com/compose/compose-file/)
