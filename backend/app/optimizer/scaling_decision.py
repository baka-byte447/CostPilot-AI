from app.cost.cost_forecast import forecast_cost
from app.rl.trainer import decide_scaling_with_rl


def decide_scaling(db):
    prediction = forecast_cost(db)

    if not isinstance(prediction, dict):
        raise ValueError("Invalid forecast response")

    if prediction.get("error"):
        raise ValueError(prediction["error"])

    try:
        cpu = float(prediction["predicted_cpu"])
        memory = float(prediction["predicted_memory"])
        requests = float(prediction["predicted_requests"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("Forecast response missing required prediction values") from exc

    decision = decide_scaling_with_rl(cpu, memory, requests)

    if isinstance(decision, dict):
        replicas = decision.get("replicas")
    else:
        replicas = decision

    if replicas is None:
        raise ValueError("RL decision did not return a replica count")

    return replicas