import logging
from dataclasses import dataclass
from statistics import mean

import numpy as np

from config import (
    FORECAST_MODEL_MIN_POINTS,
    LSTM_EPOCHS,
    LSTM_HIDDEN_SIZE,
    LSTM_LEARNING_RATE,
    LSTM_SEQUENCE_LENGTH,
    OPTIMIZER_FORECAST_HORIZON_HOURS,
)

logger = logging.getLogger(__name__)


@dataclass
class Forecast:
    resource_id: str
    resource_type: str
    region: str
    metric_name: str
    horizon_hours: int
    method: str
    current_avg: float
    current_peak: float
    predicted_avg: float
    predicted_peak: float


def forecast_metrics(metric_series_list, horizon_hours=None):
    """Generate forecasts using NumPy LSTM with Prophet fallback."""
    horizon_hours = horizon_hours or OPTIMIZER_FORECAST_HORIZON_HOURS
    forecasts = []

    for series in metric_series_list:
        values = [p.get("value") for p in series.datapoints if p.get("value") is not None]
        if len(values) < 3:
            continue

        current_avg = float(series.avg_value or 0.0)
        current_peak = float(series.max_value or 0.0)
        predicted_avg, predicted_peak, method = _forecast_values(values, series.metric_name, horizon_hours)
        forecasts.append(
            Forecast(
                resource_id=series.resource_id,
                resource_type=series.resource_type,
                region=series.region,
                metric_name=series.metric_name,
                horizon_hours=horizon_hours,
                method=method,
                current_avg=current_avg,
                current_peak=current_peak,
                predicted_avg=predicted_avg,
                predicted_peak=predicted_peak,
            )
        )

    logger.info("Generated %d forecasts", len(forecasts))
    return forecasts


def _forecast_values(values, metric_name, horizon_hours):
    recent = values[-min(len(values), 7):]
    recent_avg = float(mean(recent))

    if len(values) >= FORECAST_MODEL_MIN_POINTS:
        try:
            pred_avg, pred_peak = _forecast_numpy_lstm(values, horizon_hours)
            return _clamp_metric(metric_name, pred_avg), _clamp_metric(metric_name, pred_peak), "numpy_lstm"
        except Exception as e:
            logger.debug("LSTM forecast failed (%s), trying Prophet", e)

    try:
        pred_avg, pred_peak = _forecast_prophet(values, horizon_hours)
        return _clamp_metric(metric_name, pred_avg), _clamp_metric(metric_name, pred_peak), "prophet"
    except Exception as e:
        logger.debug("Prophet forecast failed (%s), using trend fallback", e)

    slope = 0.0
    if len(values) > 1:
        slope = (values[-1] - values[0]) / (len(values) - 1)

    next_value = values[-1] + slope * horizon_hours

    predicted_avg = _clamp_metric(metric_name, recent_avg)
    predicted_peak = _clamp_metric(metric_name, max(max(recent), next_value))

    return predicted_avg, predicted_peak, "trend_fallback"


def _forecast_numpy_lstm(values, horizon_hours):
    seq_len = max(3, min(LSTM_SEQUENCE_LENGTH, len(values) - 1))
    arr = np.array(values, dtype=np.float32)
    v_min = float(np.min(arr))
    v_max = float(np.max(arr))
    scale = max(1e-6, v_max - v_min)
    norm = (arr - v_min) / scale

    xs, ys = [], []
    for i in range(len(norm) - seq_len):
        xs.append(norm[i:i + seq_len])
        ys.append(norm[i + seq_len])
    if len(xs) < 4:
        raise ValueError("not enough sequence windows for lstm")

    xs = np.array(xs, dtype=np.float32)
    ys = np.array(ys, dtype=np.float32).reshape(-1, 1)
    hidden = max(4, LSTM_HIDDEN_SIZE)

    wf = np.random.randn(1 + hidden + 1, hidden) * 0.1
    wi = np.random.randn(1 + hidden + 1, hidden) * 0.1
    wo = np.random.randn(1 + hidden + 1, hidden) * 0.1
    wc = np.random.randn(1 + hidden + 1, hidden) * 0.1
    wy = np.random.randn(hidden + 1, 1) * 0.1

    lr = max(1e-4, float(LSTM_LEARNING_RATE))
    epochs = max(20, int(LSTM_EPOCHS))

    for _ in range(epochs):
        for i in range(len(xs)):
            seq = xs[i]
            target = ys[i]
            h = np.zeros((hidden,), dtype=np.float32)
            c = np.zeros((hidden,), dtype=np.float32)
            cache = []

            for x in seq:
                z = np.concatenate(([1.0], h, [x]))
                f = _sigmoid(z @ wf)
                inp = _sigmoid(z @ wi)
                o = _sigmoid(z @ wo)
                cand = np.tanh(z @ wc)
                c = f * c + inp * cand
                h = o * np.tanh(c)
                cache.append((z, f, inp, o, cand, c, h))

            y_hat = np.concatenate(([1.0], h)) @ wy
            err = float(y_hat - target)

            dwy = np.outer(np.concatenate(([1.0], h)), [err])
            dyh = wy[1:, 0] * err
            dz = np.zeros((1 + hidden + 1,), dtype=np.float32)
            dc_next = np.zeros((hidden,), dtype=np.float32)

            for t in reversed(range(len(cache))):
                z, f, inp, o, cand, c_t, h_t = cache[t]
                c_prev = cache[t - 1][5] if t > 0 else np.zeros((hidden,), dtype=np.float32)
                tanh_c = np.tanh(c_t)
                do = dyh * tanh_c
                do_raw = do * o * (1 - o)
                dc = dyh * o * (1 - tanh_c ** 2) + dc_next
                df = dc * c_prev
                df_raw = df * f * (1 - f)
                di = dc * cand
                di_raw = di * inp * (1 - inp)
                dcand = dc * inp
                dcand_raw = dcand * (1 - cand ** 2)

                wf -= lr * np.outer(z, df_raw)
                wi -= lr * np.outer(z, di_raw)
                wo -= lr * np.outer(z, do_raw)
                wc -= lr * np.outer(z, dcand_raw)

                dz = (wf @ df_raw) + (wi @ di_raw) + (wo @ do_raw) + (wc @ dcand_raw)
                dyh = dz[1:1 + hidden]
                dc_next = dc * f

            wy -= lr * dwy

    # Roll forward
    window = norm[-seq_len:].copy()
    preds = []
    for _ in range(max(1, horizon_hours)):
        h = np.zeros((hidden,), dtype=np.float32)
        c = np.zeros((hidden,), dtype=np.float32)
        for x in window:
            z = np.concatenate(([1.0], h, [float(x)]))
            f = _sigmoid(z @ wf)
            inp = _sigmoid(z @ wi)
            o = _sigmoid(z @ wo)
            cand = np.tanh(z @ wc)
            c = f * c + inp * cand
            h = o * np.tanh(c)
        y_hat = float(np.concatenate(([1.0], h)) @ wy)
        y_hat = max(0.0, min(1.0, y_hat))
        preds.append(y_hat)
        window = np.roll(window, -1)
        window[-1] = y_hat

    denorm = [p * scale + v_min for p in preds]
    return float(np.mean(denorm)), float(np.max(denorm))


def _forecast_prophet(values, horizon_hours):
    from prophet import Prophet
    import pandas as pd

    series = [{"ds": i, "y": float(v)} for i, v in enumerate(values)]
    df = pd.DataFrame(series)
    model = Prophet(
        daily_seasonality=False,
        weekly_seasonality=False,
        yearly_seasonality=False,
        changepoint_prior_scale=0.05,
    )
    model.fit(df)
    future = model.make_future_dataframe(periods=max(1, horizon_hours), freq="H")
    forecast = model.predict(future)
    tail = forecast.tail(max(1, horizon_hours))
    return float(tail["yhat"].mean()), float(tail["yhat"].max())


def _sigmoid(x):
    return 1.0 / (1.0 + np.exp(-np.clip(x, -50, 50)))


def _clamp_metric(metric_name, value):
    if metric_name == "CPUUtilization":
        return max(0.0, min(100.0, value))
    return max(0.0, value)
