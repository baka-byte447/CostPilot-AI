from app.ml.forecasting_model import forecast_system_metrics
from app.cost.cost_model import estimate_instances, calculate_cost

def forecast_cost(db):
    predictions = forecast_system_metrics(db)

    if "error" in predictions:
        return {
            "predicted_cpu": 50.0,
            "predicted_memory": 50.0,
            "predicted_requests": 0.1,
            "required_instances": 2,
            "predicted_hourly_cost": 0.0832,
            "forecast_available": False,
            "forecast_error": predictions["error"]
        }

    cpu_forecasts = predictions["cpu_forecast"]
    mem_forecasts = predictions["memory_forecast"]
    req_forecasts = predictions["request_forecast"]

    worst_cpu     = max(p["prediction"] for p in cpu_forecasts)
    worst_memory  = max(p["prediction"] for p in mem_forecasts)
    worst_requests = max(p["prediction"] for p in req_forecasts)

    worst_cpu     = max(0.0, min(100.0, worst_cpu))
    worst_memory  = max(0.0, min(100.0, worst_memory))
    worst_requests = max(0.0, worst_requests)

    next_cpu      = cpu_forecasts[0]["prediction"]
    next_memory   = mem_forecasts[0]["prediction"]
    next_requests = req_forecasts[0]["prediction"]

    instances = estimate_instances(worst_cpu, worst_memory, worst_requests)
    cost      = calculate_cost(instances)

    return {
        "predicted_cpu":       round(next_cpu, 2),
        "predicted_memory":    round(next_memory, 2),
        "predicted_requests":  round(next_requests, 4),
        "worst_case_cpu":      round(worst_cpu, 2),
        "worst_case_memory":   round(worst_memory, 2),
        "worst_case_requests": round(worst_requests, 4),
        "required_instances":  instances,
        "predicted_hourly_cost": round(cost, 4),
        "forecast_available":  True,
        "cpu_forecast":        cpu_forecasts,
        "memory_forecast":     mem_forecasts,
        "request_forecast":    req_forecasts,
    }

