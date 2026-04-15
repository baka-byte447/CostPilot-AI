from app.ml.forecasting_model import forecast_system_metrics
from app.cost.cost_model import estimate_instances, calculate_cost



def forecast_cost(db):
    predictions = forecast_system_metrics(db)
    cpu= predictions["cpu_forecast"][0]["prediction"]
    memory= predictions["memory_forecast"][0]["prediction"]
    request_load= predictions["request_forecast"][0]["prediction"]
    instances= estimate_instances(cpu, memory, request_load)
    cost= calculate_cost(instances)

    return {
        "predicted_cpu": cpu,
        "predicted_memory": memory,
        "predicted_requests": request_load,
        "required_instances": instances,
        "predicted_hourly_cost": cost}