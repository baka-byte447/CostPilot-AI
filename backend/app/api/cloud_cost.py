from fastapi import APIRouter
from app.cloud.aws_cost_service import get_last_day_cost

router = APIRouter()

@router.get("/aws/cost")
def get_aws_cost():
    cost = get_last_day_cost()
    return {"daily_cost": cost}


          