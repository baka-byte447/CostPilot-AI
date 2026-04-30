import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import boto3

from config import (
    AWS_REGION,
    OPTIMIZER_LOOKBACK_DAYS,
    OPTIMIZER_METRIC_PERIOD,
    OPTIMIZER_MAX_RESOURCES,
)

logger = logging.getLogger(__name__)


@dataclass
class MetricSeries:
    resource_id: str
    resource_type: str
    region: str
    metric_name: str
    namespace: str
    unit: str
    period: int
    start_time: datetime
    end_time: datetime
    datapoints: list
    avg_value: float
    max_value: float
    min_value: float


_METRIC_MAP = {
    "EC2": [
        ("AWS/EC2", "CPUUtilization", "InstanceId"),
        ("AWS/EC2", "NetworkIn", "InstanceId"),
        ("AWS/EC2", "NetworkOut", "InstanceId"),
        ("CWAgent", "mem_used_percent", "InstanceId"),
    ],
    "RDS": [
        ("AWS/RDS", "CPUUtilization", "DBInstanceIdentifier"),
        ("AWS/RDS", "DatabaseConnections", "DBInstanceIdentifier"),
        ("AWS/RDS", "FreeableMemory", "DBInstanceIdentifier"),
    ],
    "EBS": [
        ("AWS/EBS", "VolumeReadOps", "VolumeId"),
        ("AWS/EBS", "VolumeWriteOps", "VolumeId"),
    ],
}


def collect_metrics(resources, lookback_days=None, period_seconds=None, max_resources=None):
    """Collect CloudWatch metrics for active resources."""
    if not resources:
        return []

    lookback_days = lookback_days or OPTIMIZER_LOOKBACK_DAYS
    period_seconds = period_seconds or OPTIMIZER_METRIC_PERIOD
    max_resources = max_resources or OPTIMIZER_MAX_RESOURCES

    end_time = datetime.now(timezone.utc)
    start_time = end_time - timedelta(days=lookback_days)

    filtered = [r for r in resources if r.get("id") or r.get("resource_id")]
    filtered = filtered[:max_resources]

    metrics = []
    cw_clients = {}

    for r in filtered:
        r_id = r.get("id") or r.get("resource_id")
        r_type = r.get("type") or r.get("resource_type") or "Unknown"
        region = r.get("region", AWS_REGION)

        metric_defs = _METRIC_MAP.get(r_type)
        if not metric_defs:
            continue

        cw = cw_clients.get(region)
        if cw is None:
            cw = boto3.client("cloudwatch", region_name=region)
            cw_clients[region] = cw

        for namespace, metric_name, dimension_name in metric_defs:
            try:
                series = _fetch_metric_series(
                    cw,
                    namespace,
                    metric_name,
                    dimension_name,
                    r_id,
                    period_seconds,
                    start_time,
                    end_time,
                    r_type,
                    region,
                )
                if series:
                    metrics.append(series)
            except Exception as e:
                logger.debug(
                    "Metric fetch failed for %s %s %s: %s",
                    r_type,
                    r_id,
                    metric_name,
                    e,
                )

    logger.info("Collected %d metric series", len(metrics))
    return metrics


def _fetch_metric_series(
    cw,
    namespace,
    metric_name,
    dimension_name,
    resource_id,
    period_seconds,
    start_time,
    end_time,
    resource_type,
    region,
):
    resp = cw.get_metric_statistics(
        Namespace=namespace,
        MetricName=metric_name,
        Dimensions=[{"Name": dimension_name, "Value": resource_id}],
        StartTime=start_time,
        EndTime=end_time,
        Period=period_seconds,
        Statistics=["Average", "Maximum", "Minimum"],
    )

    datapoints = resp.get("Datapoints", [])
    if not datapoints:
        return None

    datapoints_sorted = sorted(datapoints, key=lambda d: d.get("Timestamp"))
    values = [d.get("Average") for d in datapoints_sorted if d.get("Average") is not None]
    if not values:
        return None

    avg_value = sum(values) / len(values)
    max_value = max(values)
    min_value = min(values)

    series_points = [
        {"timestamp": d.get("Timestamp"), "value": d.get("Average")}
        for d in datapoints_sorted
        if d.get("Average") is not None
    ]

    unit = datapoints_sorted[0].get("Unit", "") if datapoints_sorted else ""

    return MetricSeries(
        resource_id=resource_id,
        resource_type=resource_type,
        region=region,
        metric_name=metric_name,
        namespace=namespace,
        unit=unit,
        period=period_seconds,
        start_time=start_time,
        end_time=end_time,
        datapoints=series_points,
        avg_value=avg_value,
        max_value=max_value,
        min_value=min_value,
    )
