from app.cost.cost_forecast import forecast_cost
from app.rl.trainer import decide_scaling_with_rl

def decide_scaling(db):
    prediction = forecast_cost(db)

    cpu = prediction["predicted_cpu"]
    memory = prediction["predicted_memory"]
    requests = prediction["predicted_requests"]

    replicas = decide_scaling_with_rl(cpu, memory,requests)

    return replicas