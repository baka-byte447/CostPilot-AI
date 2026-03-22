from datetime import datetime, timedelta
from .aws_client import get_cost_client

def get_last_day_cost():
    client = get_cost_client()
    end = datetime.utcnow().date()
    start =end - timedelta(days=1)
    response = client.get_cost_and_usage(
        TimePeriod={
            "Start": str(start),
            "End": str(end)},
        Granularity="DAILY",
        Metrics=["UnblendedCost"])
    amount = response["ResultsByTime"][0]["Total"]["UnblendedCost"]["Amount"]
    return float(amount)


