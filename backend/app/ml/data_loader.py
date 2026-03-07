import pandas as pd
from sqlalchemy.orm import Session
from app.models.metrics_model import Metrics

def load_metrics_dataframe(db:Session):
    data = db.query(Metrics).all()
    rows = []
    for item in data:
        rows.append({
            "timestamp":item.timestamp,
            "cpu_usage":item.cpu_usage,
            "memory_usage":item.memory_usage,
            "request_load":item.request_load
        })

    df = pd.DataFrame(rows)
    if df.empty:
        return df
    df = df.sort_values("timestamp")
    return df