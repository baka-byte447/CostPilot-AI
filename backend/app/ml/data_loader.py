import pandas as pd
from sqlalchemy.orm import Session
from app.models.metrics_model import Metrics


def load_metrics_dataframe(db: Session) -> pd.DataFrame:
    data = db.query(Metrics).all()
    rows = [
        {
            "timestamp":    item.timestamp,
            "cpu_usage":    max(0.0, min(100.0, item.cpu_usage or 0.0)),
            "memory_usage": max(0.0, min(100.0, item.memory_usage or 0.0)),
            "request_load": max(0.0, item.request_load or 0.0),
        }
        for item in data
    ]
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    return df.sort_values("timestamp").reset_index(drop=True)