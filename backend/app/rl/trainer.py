from app.rl.environment import CloudEnvironment
from app.rl.agent import QLearningAgent

_env   = CloudEnvironment()
_agent = QLearningAgent()

_last_metrics = {"cpu": None, "memory": None, "request_load": None}
_last_action  = None
_last_reward  = None


def decide_scaling_with_rl(cpu: float, memory: float,
                             request_load: float,
                             forecast: dict = None) -> dict:
    global _last_metrics, _last_action, _last_reward

    from app.optimizer.safety_engine import check_action, clamp_replicas

    _env.reset(cpu, memory, request_load, forecast=forecast)

    proposed_action_idx = _agent.choose_action(cpu, memory, request_load)
    action_names        = {0: "scale_up", 1: "maintain", 2: "scale_down"}
    proposed_action     = action_names[proposed_action_idx]

    safety = check_action(
        proposed_action=proposed_action,
        current_replicas=_env.current_replicas,
        cpu=cpu,
        memory=memory,
        request_load=request_load
    )

    safe_action     = safety["safe_action"]
    safe_action_idx = {v: k for k, v in action_names.items()}[safe_action]

    _, reward, replicas = _env.step(safe_action_idx)

    if safety["blocked"]:
        reward -= 2

    if _last_metrics["cpu"] is not None:
        _agent.update(
            cpu=_last_metrics["cpu"],
            memory=_last_metrics["memory"],
            request_load=_last_metrics["request_load"],
            action=_last_action,
            reward=_last_reward,
            next_cpu=cpu,
            next_memory=memory,
            next_request_load=request_load
        )
    else:
        _agent.update(cpu, memory, request_load, safe_action_idx, reward)

    _last_metrics = {"cpu": cpu, "memory": memory, "request_load": request_load}
    _last_action  = safe_action_idx
    _last_reward  = reward

    state_idx = _agent.get_state_index(cpu, memory, request_load)

    forecast_summary = None
    if forecast and forecast.get("forecast_available"):
        forecast_summary = {
            "worst_case_cpu":      forecast.get("worst_case_cpu"),
            "worst_case_memory":   forecast.get("worst_case_memory"),
            "worst_case_requests": forecast.get("worst_case_requests"),
            "high_load_incoming":  (
                forecast.get("worst_case_cpu", 0) > 75 or
                forecast.get("worst_case_memory", 0) > 80 or
                forecast.get("worst_case_requests", 0) > 0.6
            )
        }

    return {
        "action":           safe_action,
        "proposed_action":  proposed_action,
        "action_index":     safe_action_idx,
        "replicas":         replicas,
        "reward":           round(reward, 4),
        "cpu":              round(cpu, 2),
        "memory":           round(memory, 2),
        "request_load":     round(request_load, 4),
        "epsilon":          round(_agent.epsilon, 4),
        "safety":           safety,
        "forecast":         forecast_summary,
        "state": {
            "cpu_bucket":     state_idx[0],
            "memory_bucket":  state_idx[1],
            "request_bucket": state_idx[2]
        },
        "q_values": {
            "scale_up":   round(float(_agent.q_table[state_idx][0]), 4),
            "maintain":   round(float(_agent.q_table[state_idx][1]), 4),
            "scale_down": round(float(_agent.q_table[state_idx][2]), 4)
        }
    }


def get_agent_stats() -> dict:
    from app.optimizer.safety_engine import get_slo_config
    stats = _agent.get_q_table_stats()
    return {
        "epsilon":    round(_agent.epsilon, 4),
        "alpha":      _agent.alpha,
        "gamma":      _agent.gamma,
        "model_exists": True,
        "slo_config": get_slo_config(),
        **stats
    }

