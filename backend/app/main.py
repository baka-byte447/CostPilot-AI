from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from threading import Thread
import logging

from app.config.database import engine, Base
from app.models import metrics_model, user_model
from app.models import cloud_status_model

from app.api.metrics import router as metrics_router
from app.api.forecast import router as forecast_router
from app.api.cost import router as cost_router
from app.api.optimize import router as optimize_router
from app.api.aws import router as aws_router
from app.api.azure import router as azure_router
from app.api.rl import router as rl_router
from app.api.auth import router as auth_router
from app.api.credentials import router as credentials_router

from app.utils.prometheus_metrics import REQUEST_COUNTER
from app.workers.user_metrics_collector import start_scheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s"
)
logging.getLogger("azure.core.pipeline.policies.http_logging_policy").setLevel(logging.WARNING)
logging.getLogger("azure.identity").setLevel(logging.WARNING)

app = FastAPI(title="CostPilot API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)

app.include_router(auth_router)
app.include_router(credentials_router)
app.include_router(metrics_router)
app.include_router(forecast_router)
app.include_router(cost_router)
app.include_router(optimize_router)
app.include_router(aws_router)
app.include_router(azure_router)
app.include_router(rl_router)


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