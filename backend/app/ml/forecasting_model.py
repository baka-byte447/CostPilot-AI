from datetime import datetime, timedelta, timezone

try:
    from prophet import Prophet
except Exception:  # pragma: no cover - optional dependency
    Prophet = None

from app.ml.data_loader import load_metrics_dataframe


def _is_dataframe(data):
    return hasattr(data, "__getitem__") and hasattr(data, "sort_values") and not isinstance(data, list)


def _extract_series(data, column):
    if _is_dataframe(data):
        if data.empty:
            return []
        return [float(value) for value in data[column].tolist()]

    if isinstance(data, list):
        values = []
        for item in data:
            raw = item.get(column)
            try:
                values.append(float(raw))
            except (TypeError, ValueError):
                continue
        return values

    return []


def _extract_timestamps(data):
    if _is_dataframe(data):
        if data.empty:
            return []
        return [value.to_pydatetime() if hasattr(value, "to_pydatetime") else value for value in data["timestamp"].tolist()]

    if isinstance(data, list):
        return [item.get("timestamp") for item in data if item.get("timestamp")]

    return []


def _moving_average_predictions(values, periods=6):
    if not values:
        return []

    window = min(6, len(values))
    recent = values[-window:]
    baseline = sum(recent) / len(recent)
    drift = 0.0

    if len(recent) > 1:
        drift = (recent[-1] - recent[0]) / (len(recent) - 1)

    raw_preds = [baseline + (drift * step) for step in range(1, periods + 1)]
    return [max(0.0, min(100.0, p)) for p in raw_preds]


def _fallback_forecast(data, column):
    values = _extract_series(data, column)
    timestamps = _extract_timestamps(data)
    start_time = timestamps[-1] if timestamps else datetime.now(timezone.utc)
    predictions = _moving_average_predictions(values, periods=6)

    return [
        {
            "timestamp": (start_time + timedelta(minutes=5 * index)).isoformat(),
            "prediction": float(value),
        }
        for index, value in enumerate(predictions, start=1)
    ]


def forecast_metric(data, column):
    if Prophet is None or not _is_dataframe(data):
        return _fallback_forecast(data, column)

    try:
        prophet_df = data[["timestamp", column]].rename(
            columns={
                "timestamp": "ds",
                column: "y"
            }
        )

        model = Prophet()
        model.fit(prophet_df)
        future = model.make_future_dataframe(periods=6, freq="5min")

        forecast = model.predict(future)
        predictions = forecast[["ds", "yhat"]].tail(6)
        results = []

        for _, row in predictions.iterrows():
            results.append({
                "timestamp": str(row["ds"]),
                "prediction": float(row["yhat"])
            })

        return results
    except Exception:
        return _fallback_forecast(data, column)




def forecast_system_metrics(db):

    df = load_metrics_dataframe(db)

    if len(df) < 20:
        return {"error": "Not enough data collected yet"}

    cpu_forecast = forecast_metric(df, "cpu_usage")
    memory_forecast = forecast_metric(df, "memory_usage")
    request_forecast = forecast_metric(df, "request_load")
    return {
        "cpu_forecast": cpu_forecast,
        "memory_forecast": memory_forecast,
        "request_forecast": request_forecast,
        "model": "prophet" if Prophet is not None and _is_dataframe(df) else "moving_average",
    }