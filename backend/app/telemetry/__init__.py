"""
Telemetry & Data Ingestion Module
Collects raw telemetry (CPU, memory, I/O, request load) and billing data.
Exports metrics in Prometheus format.
"""
from app.telemetry.collector import MetricsCollector, initialize_collector, get_collector
__all__ = ['MetricsCollector']
