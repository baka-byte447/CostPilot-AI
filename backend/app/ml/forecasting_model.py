import os
import logging
from datetime import datetime, timedelta
from app.ml.data_loader import load_metrics_dataframe

logger = logging.getLogger(__name__)

LSTM_MIN_ROWS  = 21
LSTM_LOOK_BACK = 20
LSTM_HIDDEN    = 16
LSTM_LR        = 0.005
LSTM_EPOCHS    = 30
MODELS_DIR     = "app/rl/models"


def _lstm_path(column: str) -> str:
    return os.path.join(MODELS_DIR, f"lstm_{column}")


def _build_timestamps(steps: int = 6):
    base = datetime.utcnow()
    return [str(base + timedelta(minutes=5 * (i + 1))) for i in range(steps)]


def forecast_metric_lstm(df, column: str, retrain: bool = False, steps: int = 6) -> list:
    from app.ml.lstm_model import LSTMForecaster

    path = _lstm_path(column)
    model_exists = os.path.exists(path + ".npz")

    if model_exists and not retrain:
        model = LSTMForecaster.load(path)
    else:
        model = LSTMForecaster(hidden_size=LSTM_HIDDEN, look_back=LSTM_LOOK_BACK, lr=LSTM_LR)
        model.fit(df[column].values, epochs=LSTM_EPOCHS)
        model.save(path)
        logger.info(f"LSTM trained and saved for column '{column}'")

    predictions = model.predict(df[column].values, steps=steps)
    timestamps  = _build_timestamps(steps)

    return [
        {"timestamp": ts, "prediction": float(max(0.0, pred))}
        for ts, pred in zip(timestamps, predictions)
    ]


def forecast_metric_prophet(df, column: str, steps: int = 6) -> list:
    from prophet import Prophet

    prophet_df = df[["timestamp", column]].rename(
        columns={"timestamp": "ds", column: "y"}
    )
    model = Prophet(daily_seasonality=False, weekly_seasonality=False, yearly_seasonality=False)
    model.fit(prophet_df)
    future   = model.make_future_dataframe(periods=steps, freq="5min")
    forecast = model.predict(future)
    rows     = forecast[["ds", "yhat"]].tail(steps)

    return [
        {"timestamp": str(row["ds"]), "prediction": float(row["yhat"])}
        for _, row in rows.iterrows()
    ]


def forecast_system_metrics(db, model: str = "auto", retrain: bool = False) -> dict:
    df = load_metrics_dataframe(db)

    if df.empty or len(df) < 2:
        return {"error": "Not enough data collected yet"}

    use_lstm = (model == "lstm") or (model == "auto" and len(df) >= LSTM_MIN_ROWS)

    if use_lstm:
        try:
            return {
                "cpu_forecast":     forecast_metric_lstm(df, "cpu_usage",    retrain=retrain),
                "memory_forecast":  forecast_metric_lstm(df, "memory_usage", retrain=retrain),
                "request_forecast": forecast_metric_lstm(df, "request_load", retrain=retrain),
                "model_used":       "lstm",
                "rows_used":        len(df)
            }
        except Exception as e:
            logger.warning(f"LSTM forecast failed ({e}), falling back to Prophet")

    if len(df) < 20:
        return {"error": "Not enough data collected yet"}

    try:
        return {
            "cpu_forecast":     forecast_metric_prophet(df, "cpu_usage"),
            "memory_forecast":  forecast_metric_prophet(df, "memory_usage"),
            "request_forecast": forecast_metric_prophet(df, "request_load"),
            "model_used":       "prophet",
            "rows_used":        len(df)
        }
    except Exception as e:
        return {"error": str(e)}