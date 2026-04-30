import logging
import os
from dataclasses import dataclass

import numpy as np

from config import RL_ALPHA, RL_EPSILON, RL_GAMMA, RL_QTABLE_PATH

logger = logging.getLogger(__name__)

_ACTIONS = ("scale_down", "maintain", "scale_up")
_ACTION_TO_IDX = {a: i for i, a in enumerate(_ACTIONS)}
_STATE_BUCKETS = 10
_STATE_SIZE = _STATE_BUCKETS ** 3


@dataclass
class RLDecision:
    resource_id: str
    resource_type: str
    region: str
    state_idx: int
    action: str
    confidence: float
    q_values: list
    cpu: float
    memory: float
    request_load: float


def build_rl_decisions(resources, metrics, forecasts):
    q_table = _load_q_table()
    metric_index = _index_series(metrics)
    forecast_index = _index_forecasts(forecasts)
    decisions = []

    for r in resources or []:
        r_type = r.get("type") or r.get("resource_type")
        if r_type not in ("EC2", "RDS"):
            continue
        r_id = r.get("id") or r.get("resource_id")
        if not r_id:
            continue

        cpu = _metric_value(r_id, "CPUUtilization", metric_index, forecast_index)
        mem = _metric_value(r_id, "mem_used_percent", metric_index, forecast_index)
        req = _request_load(r_id, metric_index, forecast_index)
        state_idx = _state_index(cpu, mem, req)

        q_values = q_table[state_idx]
        action_idx = _epsilon_greedy(q_values)
        action = _ACTIONS[action_idx]
        confidence = _confidence_from_q(q_values, action_idx)

        # Online one-step update using forecasted pressure as next state proxy.
        next_cpu = _metric_value(r_id, "CPUUtilization", metric_index, forecast_index, use_peak=True)
        next_mem = _metric_value(r_id, "mem_used_percent", metric_index, forecast_index, use_peak=True)
        next_req = _request_load(r_id, metric_index, forecast_index, use_peak=True)
        next_state = _state_index(next_cpu, next_mem, next_req)
        reward = _reward(cpu, mem, req, action)
        best_next = float(np.max(q_table[next_state]))
        old_q = float(q_table[state_idx, action_idx])
        q_table[state_idx, action_idx] = old_q + RL_ALPHA * (reward + RL_GAMMA * best_next - old_q)

        decisions.append(
            RLDecision(
                resource_id=r_id,
                resource_type=r_type,
                region=r.get("region"),
                state_idx=state_idx,
                action=action,
                confidence=round(confidence, 3),
                q_values=[round(float(v), 4) for v in q_values.tolist()],
                cpu=round(cpu, 2),
                memory=round(mem, 2),
                request_load=round(req, 2),
            )
        )

    _save_q_table(q_table)
    return decisions


def _index_series(metrics):
    idx = {}
    for series in metrics or []:
        idx[(series.resource_id, series.metric_name)] = series
    return idx


def _index_forecasts(forecasts):
    idx = {}
    for fc in forecasts or []:
        idx[(fc.resource_id, fc.metric_name)] = fc
    return idx


def _metric_value(resource_id, metric_name, metric_index, forecast_index, use_peak=False):
    fc = forecast_index.get((resource_id, metric_name))
    if fc:
        if use_peak:
            return float(fc.predicted_peak or 0.0)
        return float(fc.predicted_avg or 0.0)
    series = metric_index.get((resource_id, metric_name))
    if not series:
        return 0.0
    return float(series.max_value if use_peak else series.avg_value or 0.0)


def _request_load(resource_id, metric_index, forecast_index, use_peak=False):
    network_in = _metric_value(resource_id, "NetworkIn", metric_index, forecast_index, use_peak=use_peak)
    network_out = _metric_value(resource_id, "NetworkOut", metric_index, forecast_index, use_peak=use_peak)
    raw = max(0.0, network_in + network_out)
    return min(3.0, np.log1p(raw) / 10.0)


def _state_index(cpu, memory, request_load):
    cpu_b = _bucket(cpu, 100.0)
    mem_b = _bucket(memory, 100.0)
    req_b = _bucket(request_load, 3.0)
    return cpu_b * (_STATE_BUCKETS ** 2) + mem_b * _STATE_BUCKETS + req_b


def _bucket(value, max_value):
    clipped = max(0.0, min(float(max_value), float(value)))
    idx = int((clipped / max_value) * (_STATE_BUCKETS - 1))
    return max(0, min(_STATE_BUCKETS - 1, idx))


def _epsilon_greedy(q_values):
    if np.random.random() < RL_EPSILON:
        return int(np.random.randint(0, len(_ACTIONS)))
    return int(np.argmax(q_values))


def _confidence_from_q(q_values, action_idx):
    best = float(q_values[action_idx])
    spread = float(np.max(q_values) - np.min(q_values))
    return min(0.98, max(0.5, 0.5 + (best + spread) / 4.0))


def _reward(cpu, memory, request_load, action):
    target_cpu = 50.0
    target_mem = 60.0
    target_req = 1.0

    utilization_penalty = abs(cpu - target_cpu) / 100.0 + abs(memory - target_mem) / 100.0
    pressure_penalty = abs(request_load - target_req) / 3.0
    action_bias = {"scale_down": 0.15, "maintain": 0.1, "scale_up": -0.05}[action]

    if cpu > 85 or memory > 90 or request_load > 2.0:
        action_bias = -0.4 if action == "scale_down" else (0.2 if action == "scale_up" else -0.1)
    if cpu < 15 and memory < 25 and request_load < 0.3:
        action_bias = 0.3 if action == "scale_down" else (0.15 if action == "maintain" else -0.2)

    return float(action_bias - utilization_penalty - pressure_penalty)


def _load_q_table():
    if os.path.exists(RL_QTABLE_PATH):
        try:
            table = np.load(RL_QTABLE_PATH)
            if table.shape == (_STATE_SIZE, len(_ACTIONS)):
                return table
        except Exception as e:
            logger.warning("Failed loading RL q-table: %s", e)
    return np.zeros((_STATE_SIZE, len(_ACTIONS)), dtype=np.float32)


def _save_q_table(table):
    try:
        directory = os.path.dirname(RL_QTABLE_PATH)
        if directory:
            os.makedirs(directory, exist_ok=True)
        np.save(RL_QTABLE_PATH, table)
    except Exception as e:
        logger.warning("Failed saving RL q-table: %s", e)
