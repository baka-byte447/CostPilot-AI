from datetime import datetime, timezone

from app.rl.environment import CloudEnvironment
from app.rl.agent import QLearningAgent
from app.optimizer.safety_engine import (
    check_action,
    clamp_replicas,
    get_last_replicas,
    record_replicas,
)


env = CloudEnvironment()
agent = QLearningAgent()

ACTION_LABELS = {
    0: "scale_down",
    1: "maintain",
    2: "scale_up",
}


def _to_float(value, fallback=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return float(fallback)


def _bucket(value, size, max_bucket=None):
    try:
        idx = int(float(value) // size)
    except (TypeError, ValueError):
        idx = 0
    if max_bucket is not None:
        idx = min(max_bucket, max(0, idx))
    return idx


def _get_q_values(cpu, memory, request_load):
    state_key = agent._get_state_key(cpu, memory, request_load)
    scores = agent.q_table.get(state_key)
    if not scores or len(scores) < len(agent.action_space):
        scores = [0.0 for _ in agent.action_space]
    return {
        "scale_down": float(scores[0]),
        "maintain": float(scores[1]),
        "scale_up": float(scores[2]),
    }


def decide_scaling_with_rl(cpu, memory, request_load):
    cpu = _to_float(cpu)
    memory = _to_float(memory)
    request_load = _to_float(request_load)

    env.reset(cpu, memory, request_load)
    action_index = agent.choose_action(cpu, memory, request_load)
    _, reward, proposed_replicas = env.step(action_index)
    agent.update(cpu, memory, request_load, action_index, reward, cpu, memory, request_load)

    proposed_action = ACTION_LABELS.get(action_index, "maintain")
    current_replicas = get_last_replicas()

    safety = check_action(proposed_action, current_replicas, cpu, memory, request_load)
    safe_action = safety.get("safe_action", proposed_action)

    if safe_action == proposed_action:
        safe_replicas = clamp_replicas(current_replicas, proposed_replicas)
    elif safe_action == "scale_up":
        safe_replicas = clamp_replicas(current_replicas, current_replicas + 1)
    elif safe_action == "scale_down":
        safe_replicas = clamp_replicas(current_replicas, current_replicas - 1)
    else:
        safe_replicas = current_replicas

    record_replicas(safe_replicas)

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "action": safe_action,
        "proposed_action": proposed_action,
        "action_index": action_index,
        "replicas": safe_replicas,
        "reward": reward,
        "epsilon": agent.epsilon,
        "q_values": _get_q_values(cpu, memory, request_load),
        "cpu": cpu,
        "memory": memory,
        "request_load": request_load,
        "state": {
            "cpu_bucket": _bucket(cpu, 10, 9),
            "memory_bucket": _bucket(memory, 10, 9),
            "request_bucket": _bucket(request_load, 0.1),
        },
        "safety": safety,
    }


def get_agent_stats():
    total_states = 1000
    visited_states = len(agent.q_table)
    scores = []
    nonzero_entries = 0

    for values in agent.q_table.values():
        for value in values:
            v = float(value)
            scores.append(v)
            if abs(v) > 1e-9:
                nonzero_entries += 1

    max_q = max(scores) if scores else 0.0
    mean_q = sum(scores) / len(scores) if scores else 0.0
    coverage_pct = round((visited_states / total_states) * 100, 1) if total_states else 0.0

    return {
        "shape": [total_states, len(agent.action_space)],
        "total_states": total_states,
        "visited_states": visited_states,
        "coverage_pct": coverage_pct,
        "nonzero_entries": nonzero_entries,
        "max_q_value": max_q,
        "mean_q_value": mean_q,
        "alpha": agent.alpha,
        "gamma": agent.gamma,
        "epsilon": agent.epsilon,
    }