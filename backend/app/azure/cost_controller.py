import logging
import os
from datetime import datetime,timezone,timedelta
from .azure_client import azure

logger=logging.getLogger(__name__)


class AzureCostController:

    def __init__(self):
        self.subscription_id = os.getenv("AZURE_SUBSCRIPTION_ID")
        self.scope=f"/subscriptions/{self.subscription_id}"

    def get_current_month_cost(self)->dict:

        from azure.mgmt.costmanagement.models import(
            QueryDefinition,QueryTimePeriod,
            QueryDataset,QueryAggregation,QueryGrouping
        )

        now=datetime.now(timezone.utc)
        start = now.replace(day=1,hour=0,minute=0,second=0,microsecond=0)

        cost_client=azure.cost()

        query=QueryDefinition(
            type="ActualCost",
            timeframe="Custom",
            time_period=QueryTimePeriod(
                from_property=start,
                to=now
            ),
            dataset=QueryDataset(
                granularity="None",
                aggregation={
                    "totalCost":QueryAggregation(
                        name="PreTaxCost",
                        function="Sum"
                    )
                }
            )
        )

        result = cost_client.query.usage(self.scope,query)

        rows=result.rows
        total=float(rows[0][0]) if rows else 0.0

        return{
            "amount": round(total,4),
            "currency":"USD",
            "period_start":start.strftime("%Y-%m-%d"),
            "period_end": now.strftime("%Y-%m-%d")
        }

    def get_cost_by_service(self,days:int=7)->list:

        from azure.mgmt.costmanagement.models import(
            QueryDefinition,QueryTimePeriod,QueryDataset,
            QueryAggregation,QueryGrouping
        )

        now = datetime.now(timezone.utc)
        start=now - timedelta(days=days)

        cost_client = azure.cost()

        query = QueryDefinition(
            type="ActualCost",
            timeframe="Custom",
            time_period=QueryTimePeriod(from_property=start,to=now),
            dataset=QueryDataset(
                granularity="Daily",
                aggregation={
                    "totalCost": QueryAggregation(
                        name="PreTaxCost",function="Sum"
                    )
                },
                grouping=[
                    QueryGrouping(type="Dimension",name="ServiceName")
                ]
            )
        )

        result=cost_client.query.usage(self.scope, query)

        breakdown={}

        for row in result.rows:

            cost=round(float(row[0]),4)
            service = row[1]

            breakdown[service]=breakdown.get(service,0)+cost

        return[
            {"service":k,"cost":v}
            for k,v in sorted(breakdown.items(),key=lambda x:-x[1])
        ]