import requests
from sqlalchemy.orm import Session
from app.models.metrics_model import Metrics
from datetime import datetime

PROMETHEUS_URL = "http://prometheus:9090"

CPU_QUERY = '100 - (avg by(instance)(rate(node_cpu_seconds_total{mode="idle"}[1m])) * 100)'
MEMORY_QUERY = '(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes))* 100'
REQUEST_QUERY = 'rate(app_requests_total[1m])'

def fetch_prometheus_data(query:str):
    response = requests.get(f"{PROMETHEUS_URL}/api/v1/query", params={"query":query})
    data = response.json()

    try:
        return float(data["data"]["result"][0]["value"][1])
    except:
        return 0.0
    
def collect_and_store_metrics(db: Session):
    cpu = fetch_prometheus_data(CPU_QUERY)
    memory = fetch_prometheus_data(MEMORY_QUERY)
    requests_per_sec = fetch_prometheus_data(REQUEST_QUERY)

    metric = Metrics(cpu_usage=cpu, memory_usage=memory ,request_load=requests_per_sec, timestamp=datetime.utcnow())
    
    db.add(metric)
    db.commit()
    db.refresh(metric)

    return {
        "cpu_usage" : cpu, "memory_usage" : memory, "request_load":requests_per_sec, "timestamp": metric.timestamp
    }

def get_all_metrics(db: Session):
    return db.query(Metrics).all()

