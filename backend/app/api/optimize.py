from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.config.database import SessionLocal
from app.k8s.k8s_controller import scale_deployment
from app.optimizer.scaling_decision import decide_scaling

router = APIRouter(prefix="/optimize", tags=["optimize"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/scale", summary="Choose replica count via RL and apply to Kubernetes")
def optimize_cluster(db: Session = Depends(get_db)):
    try:
        replicas = decide_scaling(db)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to decide scaling: {exc}") from exc

    try:
        result = scale_deployment(
            deployment_name="load-test-app",
            namespace="default",
            replicas=replicas,
        )
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Failed to scale Kubernetes deployment: {exc}") from exc

    return result


@router.get("/preview", summary="Preview the recommended replica count without applying scaling")
def preview_scaling(db: Session = Depends(get_db)):
    try:
        replicas = decide_scaling(db)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to preview scaling: {exc}") from exc

    return {
        "deployment": "load-test-app",
        "recommended_replicas": replicas,
        "mode": "preview",
    }





