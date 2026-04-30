"""Lightweight demand forecasting helper.

Uses a simple moving-average baseline so the system has a predictable,
human-auditable forecast when richer models are not available.

DEPRECATED: This module is deprecated. Use backend/app/ml/forecasting_model.py instead.
"""

import warnings
warnings.warn("DemandPredictor is deprecated and no longer used. See ml/forecasting_model.py.", DeprecationWarning, stacklevel=2)

from statistics import mean
from typing import Iterable, List, Optional, Sequence


class DemandPredictor:
    """Predict future resource demand using a moving-average baseline."""

    def __init__(self, window: int = 12):
        self.window = window
        self.history: List[float] = []
        self.last_forecast: List[float] = []
        self.last_errors = {"mape": None, "mse": None}

    def train(self, historical_data: Iterable[float]) -> dict:
        """Store a sanitized slice of historical points for forecasting."""
        self.history = [float(x) for x in historical_data if x is not None]
        return {"points_ingested": len(self.history)}

    def predict(self, hours_ahead: int = 1) -> List[float]:
        """Predict the next `hours_ahead` points using a rolling mean."""
        if not self.history or hours_ahead <= 0:
            return []

        window_slice = self.history[-self.window :] or self.history
        baseline = mean(window_slice)
        self.last_forecast = [baseline for _ in range(hours_ahead)]
        return self.last_forecast

    def get_forecast_accuracy(self, actuals: Optional[Sequence[float]] = None) -> dict:
        """Return basic error metrics when actuals are provided."""
        if not actuals or not self.last_forecast:
            return self.last_errors

        paired = list(zip(self.last_forecast, actuals))
        if not paired:
            return self.last_errors

        mse = sum((f - a) ** 2 for f, a in paired) / len(paired)
        mape_components = [abs((a - f) / a) for f, a in paired if a]
        mape = sum(mape_components) / len(mape_components) if mape_components else None

        self.last_errors = {"mape": mape, "mse": mse}
        return self.last_errors
