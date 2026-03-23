
import logging
from datetime import datetime, timedelta
from .aws_client import aws

logger = logging.getLogger(__name__)


class CostExplorer:
    """
    Pulls real cost data from AWS Cost Explorer API.
    Use this to feed actual spend numbers into the RL reward function
    instead of estimated costs.
    """

    def get_daily_cost(self, days: int = 7) -> list:
        """
        Returns daily cost breakdown for the last N days.
        Grouped by service so you can see EC2 vs ECS vs EKS spend.
        """
        end = datetime.utcnow().date()
        start = end - timedelta(days=days)

        resp = aws.cost_explorer().get_cost_and_usage(
            TimePeriod={
                "Start": start.strftime("%Y-%m-%d"),
                "End": end.strftime("%Y-%m-%d")
            },
            Granularity="DAILY",
            Metrics=["UnblendedCost"],
            GroupBy=[{"Type": "DIMENSION", "Key": "SERVICE"}]
        )

        results = []
        for period in resp.get("ResultsByTime", []):
            day = {
                "date": period["TimePeriod"]["Start"],
                "total": 0.0,
                "by_service": {}
            }
            for group in period.get("Groups", []):
                service = group["Keys"][0]
                amount = float(group["Metrics"]["UnblendedCost"]["Amount"])
                day["by_service"][service] = round(amount, 4)
                day["total"] += amount
            day["total"] = round(day["total"], 4)
            results.append(day)

        return results

    def get_current_month_cost(self) -> dict:
        """Returns total spend so far this calendar month."""
        now = datetime.utcnow().date()
        start = now.replace(day=1)

        resp = aws.cost_explorer().get_cost_and_usage(
            TimePeriod={
                "Start": start.strftime("%Y-%m-%d"),
                "End": now.strftime("%Y-%m-%d")
            },
            Granularity="MONTHLY",
            Metrics=["UnblendedCost", "UsageQuantity"]
        )

        periods = resp.get("ResultsByTime", [])
        if not periods:
            return {"amount": 0.0, "currency": "USD"}

        amount = float(periods[0]["Total"]["UnblendedCost"]["Amount"])
        return {
            "amount": round(amount, 2),
            "currency": "USD",
            "period_start": start.strftime("%Y-%m-%d"),
            "period_end": now.strftime("%Y-%m-%d")
        }

    def get_cost_forecast(self, days_ahead: int = 30) -> dict:
        """Uses AWS's own ML forecast for end-of-month projected spend."""
        now = datetime.utcnow().date()
        end = now + timedelta(days=days_ahead)

        resp = aws.cost_explorer().get_cost_forecast(
            TimePeriod={
                "Start": (now + timedelta(days=1)).strftime("%Y-%m-%d"),
                "End": end.strftime("%Y-%m-%d")
            },
            Metric="UNBLENDED_COST",
            Granularity="MONTHLY"
        )

        total = resp.get("Total", {})
        return {
            "forecast_amount": round(float(total.get("Amount", 0)), 2),
            "currency": total.get("Unit", "USD"),
            "forecast_days": days_ahead
        }
    
