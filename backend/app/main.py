from fastapi import FastAPI, Request
from app.api.metrics import router as metrics_router
from app.config.database import engine, Base
from app.api.forecast import router as forecast_router

from prometheus_client import generate_latest
from prometheus_client import CONTENT_TYPE_LATEST
from fastapi.responses import Response
from app.utils.prometheus_metrics import REQUEST_COUNTER
from threading import Thread
from app.workers.metrics_collector import start_scheduler
app = FastAPI()

Base.metadata.create_all(bind=engine)
app.include_router(metrics_router)
app.include_router(forecast_router)

@app.on_event("startup")
def start_background_worker():
    thread = Thread(target=start_scheduler)
    thread.daemon = True
    thread.start()

@app.middleware("http")
async def count_requests(request: Request, call_next):
    REQUEST_COUNTER.inc()
    response = await call_next(request)
    return response

@app.get("/app_metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)