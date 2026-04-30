"""
Metrics Collector for CostPilot-AI
Collects CPU, memory, I/O, network, and request metrics from system and services.
Exposes metrics in Prometheus format.
"""

import psutil
import time
from datetime import datetime, timezone
from typing import Dict, List, Any
from prometheus_client import Counter, Gauge, Histogram, start_http_server
import logging

logger = logging.getLogger(__name__)


class MetricsCollector:
    """
    Collects system and application metrics.
    Integrates with Prometheus for time-series storage.
    """
    
    def __init__(self, app_name: str = "costpilot-backend"):
        self.app_name = app_name
        self.start_time = time.time()
        
        # Define Prometheus metrics
        
        # System metrics
        self.cpu_usage = Gauge(
            'system_cpu_usage_percent',
            'CPU usage percentage',
            ['host']
        )
        
        self.memory_usage = Gauge(
            'system_memory_usage_bytes',
            'Memory usage in bytes',
            ['host', 'type']  # type: used, available, total
        )
        
        self.memory_percent = Gauge(
            'system_memory_percent',
            'Memory usage percentage',
            ['host']
        )
        
        self.disk_usage = Gauge(
            'system_disk_usage_bytes',
            'Disk usage in bytes',
            ['host', 'mount_point', 'type']  # type: used, free, total
        )
        
        self.disk_io_reads = Counter(
            'system_disk_io_reads_total',
            'Total disk read operations',
            ['host', 'device']
        )
        
        self.disk_io_writes = Counter(
            'system_disk_io_writes_total',
            'Total disk write operations',
            ['host', 'device']
        )
        
        self.network_bytes_sent = Gauge(
            'system_network_bytes_sent_total',
            'Total bytes sent over network',
            ['host', 'interface']
        )
        
        self.network_bytes_recv = Gauge(
            'system_network_bytes_received_total',
            'Total bytes received over network',
            ['host', 'interface']
        )
        
        # Application metrics
        self.api_requests_total = Counter(
            'api_requests_total',
            'Total API requests',
            ['method', 'endpoint', 'status']
        )
        
        self.api_request_duration = Histogram(
            'api_request_duration_seconds',
            'API request duration in seconds',
            ['method', 'endpoint'],
            buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0)
        )
        
        self.api_request_size = Histogram(
            'api_request_size_bytes',
            'API request size in bytes',
            ['method', 'endpoint']
        )
        
        self.api_response_size = Histogram(
            'api_response_size_bytes',
            'API response size in bytes',
            ['method', 'endpoint']
        )
        
        # Health metrics
        self.uptime = Gauge(
            'application_uptime_seconds',
            'Application uptime in seconds'
        )
        
        self.telemetry_scrapes = Counter(
            'telemetry_scrapes_total',
            'Total telemetry collection cycles'
        )
        
        logger.info(f"MetricsCollector initialized for {app_name}")
    
    def collect_system_metrics(self, hostname: str = "localhost") -> Dict[str, Any]:
        """
        Collect system-level metrics: CPU, memory, disk, network.
        
        Returns:
            Dict containing collected metrics
        """
        metrics = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'hostname': hostname,
            'cpu': self._collect_cpu_metrics(hostname),
            'memory': self._collect_memory_metrics(hostname),
            'disk': self._collect_disk_metrics(hostname),
            'network': self._collect_network_metrics(hostname),
        }
        
        self.telemetry_scrapes.inc()
        return metrics
    
    def _collect_cpu_metrics(self, hostname: str) -> Dict[str, Any]:
        """Collect CPU metrics."""
        cpu_percent = psutil.cpu_percent(interval=1, percpu=False)
        cpu_count = psutil.cpu_count()
        
        self.cpu_usage.labels(host=hostname).set(cpu_percent)
        
        return {
            'usage_percent': cpu_percent,
            'count': cpu_count,
            'per_cpu': psutil.cpu_percent(interval=0.1, percpu=True)
        }
    
    def _collect_memory_metrics(self, hostname: str) -> Dict[str, Any]:
        """Collect memory metrics."""
        mem = psutil.virtual_memory()
        
        self.memory_usage.labels(host=hostname, type='used').set(mem.used)
        self.memory_usage.labels(host=hostname, type='available').set(mem.available)
        self.memory_usage.labels(host=hostname, type='total').set(mem.total)
        self.memory_percent.labels(host=hostname).set(mem.percent)
        
        return {
            'used_bytes': mem.used,
            'available_bytes': mem.available,
            'total_bytes': mem.total,
            'percent': mem.percent
        }
    
    def _collect_disk_metrics(self, hostname: str) -> Dict[str, Any]:
        """Collect disk metrics."""
        disk_metrics = {}
        
        for partition in psutil.disk_partitions():
            mount_point = partition.mountpoint
            try:
                usage = psutil.disk_usage(mount_point)
                
                self.disk_usage.labels(
                    host=hostname,
                    mount_point=mount_point,
                    type='used'
                ).set(usage.used)
                self.disk_usage.labels(
                    host=hostname,
                    mount_point=mount_point,
                    type='free'
                ).set(usage.free)
                self.disk_usage.labels(
                    host=hostname,
                    mount_point=mount_point,
                    type='total'
                ).set(usage.total)
                
                disk_metrics[mount_point] = {
                    'used': usage.used,
                    'free': usage.free,
                    'total': usage.total,
                    'percent': usage.percent
                }
            except PermissionError:
                logger.warning(f"Permission denied for disk metrics at {mount_point}")
        
        return disk_metrics
    
    def _collect_network_metrics(self, hostname: str) -> Dict[str, Any]:
        """Collect network metrics."""
        net_io = psutil.net_io_counters(pernic=True)
        network_metrics = {}
        
        for interface, stats in net_io.items():
            self.network_bytes_sent.labels(host=hostname, interface=interface).set(stats.bytes_sent)
            self.network_bytes_recv.labels(host=hostname, interface=interface).set(stats.bytes_recv)
            
            network_metrics[interface] = {
                'bytes_sent': stats.bytes_sent,
                'bytes_recv': stats.bytes_recv,
                'packets_sent': stats.packets_sent,
                'packets_recv': stats.packets_recv,
                'errors_in': stats.errin,
                'errors_out': stats.errout,
                'dropped_in': stats.dropin,
                'dropped_out': stats.dropout
            }
        
        return network_metrics
    
    def update_uptime(self):
        """Update application uptime metric."""
        uptime = time.time() - self.start_time
        self.uptime.set(uptime)
    
    def record_api_request(
        self,
        method: str,
        endpoint: str,
        status_code: int,
        duration: float,
        request_size: int = 0,
        response_size: int = 0
    ):
        """
        Record an API request metric.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            status_code: HTTP response status code
            duration: Request duration in seconds
            request_size: Request body size in bytes
            response_size: Response body size in bytes
        """
        self.api_requests_total.labels(
            method=method,
            endpoint=endpoint,
            status=status_code
        ).inc()
        
        self.api_request_duration.labels(
            method=method,
            endpoint=endpoint
        ).observe(duration)
        
        if request_size > 0:
            self.api_request_size.labels(
                method=method,
                endpoint=endpoint
            ).observe(request_size)
        
        if response_size > 0:
            self.api_response_size.labels(
                method=method,
                endpoint=endpoint
            ).observe(response_size)
    
    def start_prometheus_server(self, port: int = 8001):
        """
        Start Prometheus metrics HTTP server.
        
        Args:
            port: Port to expose metrics on (default 8001)
        """
        try:
            start_http_server(port)
            logger.info(f"Prometheus metrics server started on port {port}")
        except Exception as e:
            logger.error(f"Failed to start Prometheus server: {e}")
            raise
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get a summary of current metrics."""
        self.update_uptime()
        
        return {
            'app_name': self.app_name,
            'uptime_seconds': time.time() - self.start_time,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }


# Global metrics collector instance
_collector = None


def get_collector() -> MetricsCollector:
    """Get or create global metrics collector."""
    global _collector
    if _collector is None:
        _collector = MetricsCollector()
    return _collector


def initialize_collector(app_name: str = "costpilot-backend") -> MetricsCollector:
    """Initialize global metrics collector."""
    global _collector
    _collector = MetricsCollector(app_name)
    return _collector
