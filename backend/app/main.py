<<<<<<< HEAD
"""
CostPilot-AI Backend Main Application
FastAPI application with integrated telemetry and metrics collection.
"""

import logging
import time
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, Request, Response
from fastapi.responses import PlainTextResponse
from prometheus_client import generate_latest

from app.telemetry import MetricsCollector, initialize_collector, get_collector

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global metrics collector
metrics_collector: Optional[MetricsCollector] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for FastAPI.
    Handles startup and shutdown events.
    """
    # Startup
    logger.info("Starting CostPilot-AI Backend...")
    global metrics_collector
    metrics_collector = initialize_collector("costpilot-backend")
    
    # Start Prometheus metrics server
    try:
        metrics_collector.start_prometheus_server(port=8001)
    except Exception as e:
        logger.warning(f"Could not start Prometheus server on port 8001: {e}")
    
    logger.info("Application startup complete")
    yield
    
    # Shutdown
    logger.info("Shutting down CostPilot-AI Backend...")


# Create FastAPI application
app = FastAPI(
    title="CostPilot-AI",
    description="Automated Cloud Cost Intelligence & Optimization",
    version="1.0.0",
    lifespan=lifespan
)


# Middleware to track API requests
@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    """Middleware to record API metrics."""
    if request.url.path == "/metrics":
        # Don't track metrics endpoint itself
        return await call_next(request)
    
    start_time = time.time()
    request_body_size = len(await request.body()) if request.method in ["POST", "PUT", "PATCH"] else 0
    
    response = await call_next(request)
    
    duration = time.time() - start_time
    response_size = int(response.headers.get("content-length", 0)) if response.headers.get("content-length") else 0
    
    # Record metrics
    collector = get_collector()
    if collector:
        collector.record_api_request(
            method=request.method,
            endpoint=request.url.path,
            status_code=response.status_code,
            duration=duration,
            request_size=request_body_size,
            response_size=response_size
        )
    
    return response


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    collector = get_collector()
    if collector:
        collector.update_uptime()
    
    return {
        "status": "healthy",
        "service": "costpilot-backend",
        "version": "1.0.0"
    }


# Metrics endpoint - Prometheus format
@app.get("/metrics", response_class=PlainTextResponse)
async def metrics():
    """
    Prometheus metrics endpoint.
    Exposes all collected metrics in Prometheus text format.
    
    Access at: http://localhost:8000/metrics
    """
    return generate_latest()


# System metrics endpoint
@app.get("/api/system-metrics")
async def get_system_metrics():
    """
    Get current system metrics as JSON.
    Includes CPU, memory, disk, and network statistics.
    """
    collector = get_collector()
    if not collector:
        return {"error": "Metrics collector not initialized"}
    
    metrics_data = collector.collect_system_metrics()
    metrics_data['summary'] = collector.get_metrics_summary()
    
    return metrics_data


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API documentation."""
    return {
        "name": "CostPilot-AI",
        "description": "Automated Cloud Cost Intelligence & Optimization Platform",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "metrics_prometheus": "/metrics",
            "metrics_json": "/api/system-metrics",
            "docs": "/docs",
            "redoc": "/redoc"
        }
    }


# Startup event handler
@app.on_event("startup")
async def startup_event():
    """Called when application starts."""
    logger.info("CostPilot-AI Backend is starting...")
    collector = get_collector()
    if collector:
        # Collect initial metrics
        collector.collect_system_metrics()
        logger.info("Initial metrics collected")


# Shutdown event handler
@app.on_event("shutdown")
async def shutdown_event():
    """Called when application shuts down."""
    logger.info("CostPilot-AI Backend is shutting down...")


if __name__ == "__main__":
    import uvicorn
    
    logger.info("Starting Uvicorn server...")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
        access_log=True
    )
=======
from fastapi import FastAPI, Request
from app.api.metrics import router as metrics_router
from app.config.database import engine, Base
from app.api.forecast import router as forecast_router
from app.api.cost import router as cost_router
from app.api.optimize import router as optimize_router

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
app.include_router(cost_router)
app.include_router(optimize_router)

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
>>>>>>> 28ba8b2a917721cbe4d390a8c72af6b0b8c8ad55
