"""
CostPilot-AI Backend Main Application
FastAPI application with telemetry, forecasting, and optimization endpoints.
"""

import logging
import time
from contextlib import asynccontextmanager
from threading import Thread
from typing import Optional

from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from app.api.cost import router as cost_router
from app.api.forecast import router as forecast_router
from app.api.metrics import router as metrics_router
from app.api.optimize import router as optimize_router
from app.config.database import Base, engine
from app.config.settings import settings
from app.telemetry import MetricsCollector, get_collector, initialize_collector
from app.workers.metrics_collector import start_scheduler


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

metrics_collector: Optional[MetricsCollector] = None
scheduler_thread: Optional[Thread] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup/shutdown for the FastAPI app."""
    global metrics_collector, scheduler_thread

    logger.info("Starting CostPilot-AI backend…")
    Base.metadata.create_all(bind=engine)

    metrics_collector = initialize_collector(settings.app_name)
    try:
        metrics_collector.start_prometheus_server(port=settings.prometheus_export_port)
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("Prometheus sidecar failed to start on port %s: %s", settings.prometheus_export_port, exc)

    scheduler_thread = Thread(target=start_scheduler, daemon=True)
    scheduler_thread.start()

    logger.info("Application startup complete")
    yield
    logger.info("Shutting down CostPilot-AI backend…")


app = FastAPI(
    title="CostPilot-AI",
    description="Automated Cloud Cost Intelligence & Optimization",
    version="1.0.0",
    lifespan=lifespan,
)


@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    """Record API metrics while skipping the Prometheus scrape endpoint."""
    if request.url.path in {"/metrics", "/health"}:
        return await call_next(request)

    start_time = time.time()
    body = await request.body()
    response = await call_next(request)

    duration = time.time() - start_time
    response_size = int(response.headers.get("content-length", len(getattr(response, "body", b""))))

    collector = get_collector()
    if collector:
        collector.record_api_request(
            method=request.method,
            endpoint=request.url.path,
            status_code=response.status_code,
            duration=duration,
            request_size=len(body) if body else 0,
            response_size=response_size,
        )

    return response


@app.get("/health")
async def health_check():
    """Lightweight health endpoint used by monitors and probes."""
    collector = get_collector()
    if collector:
        collector.update_uptime()

    return {
        "status": "healthy",
        "service": settings.app_name,
        "version": app.version,
    }


@app.get("/metrics", response_class=PlainTextResponse)
async def metrics() -> Response:
    """Expose Prometheus metrics collected inside the process."""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/api/system-metrics")
async def get_system_metrics():
    """Return current system metrics in JSON for quick debugging."""
    collector = get_collector()
    if not collector:
        return {"error": "Metrics collector not initialized"}

    metrics_data = collector.collect_system_metrics()
    metrics_data["summary"] = collector.get_metrics_summary()
    return metrics_data


@app.get("/")
async def root():
    """Entry endpoint that lists the major API surfaces."""
    return {
        "name": "CostPilot-AI",
        "description": "Automated Cloud Cost Intelligence & Optimization Platform",
        "version": app.version,
        "endpoints": {
            "health": "/health",
            "metrics_prometheus": "/metrics",
            "metrics_json": "/api/system-metrics",
            "metrics_api": "/api/metrics",
            "forecast": "/api/forecast/system",
            "cost": "/api/cost/forecast",
            "optimize": "/api/optimize/scale",
            "docs": "/docs",
            "redoc": "/redoc",
        },
    }


app.include_router(metrics_router, prefix="/api")
app.include_router(forecast_router, prefix="/api")
app.include_router(cost_router, prefix="/api")
app.include_router(optimize_router, prefix="/api")


if __name__ == "__main__":
    import uvicorn

    logger.info("Starting Uvicorn server…")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
        access_log=True,
    )
