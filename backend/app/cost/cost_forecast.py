from app.cost.cost_model import calculate_cost, estimate_instances
from app.ml.forecasting_model import forecast_system_metrics


def forecast_cost(db):
    predictions = forecast_system_metrics(db)

    if isinstance(predictions, dict) and predictions.get("error"):
        return predictions

    cpu_forecast = predictions.get("cpu_forecast", [])
    memory_forecast = predictions.get("memory_forecast", [])
    request_forecast = predictions.get("request_forecast", [])

    if not (cpu_forecast and memory_forecast and request_forecast):
        return {"error": "No forecast data available"}

    cpu = cpu_forecast[0].get("prediction", 0.0)
    memory = memory_forecast[0].get("prediction", 0.0)
    request_load = request_forecast[0].get("prediction", 0.0)

    instances = estimate_instances(cpu, memory, request_load)
    cost = calculate_cost(instances)

    return {
        "predicted_cpu": cpu,
        "predicted_memory": memory,
        "predicted_requests": request_load,
        "required_instances": instances,
        "predicted_hourly_cost": cost,
        "cpu_forecast": cpu_forecast,
        "memory_forecast": memory_forecast,
        "request_forecast": request_forecast,
    }