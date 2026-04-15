from sqlalchemy.orm import Session
from app.models.metrics_model import Metrics

try:
    import pandas as pd
except Exception:  # pragma: no cover - optional dependency
    pd = None

def load_metrics_dataframe(db: Session):
    data = db.query(Metrics).all()
    rows = []
    for item in data:
        rows.append({
            "timestamp": item.timestamp,
            "cpu_usage": item.cpu_usage,
            "memory_usage": item.memory_usage,
            "request_load": item.request_load
        })

    rows.sort(key=lambda row: row.get("timestamp") or 0)

    if pd is None:
        return rows

    df = pd.DataFrame(rows)
    if df.empty:
        return df
    df = df.sort_values("timestamp")
    return df