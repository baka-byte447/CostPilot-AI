from prometheus_client import Counter, generate_latest
from prometheus_client import CONTENT_TYPE_LATEST

REQUEST_COUNTER = Counter(
    "app_requests_total",
    "Total number of requests received"
)

def metrics_response():
    return generate_latest()