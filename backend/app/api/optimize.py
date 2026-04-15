from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.config.database import SessionLocal
from app.optimizer.scaling_decision import decide_scaling
from app.k8s.k8s_controller import scale_deployment

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/optimize/scale")
def optimize_cluster(db: Session = Depends(get_db)):

    replicas = decide_scaling(db)
    result = scale_deployment(
        deployment_name="load-test-app",
        namespace="default",
        replicas=replicas
    )

    return result




