from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.config.database import SessionLocal
from app.services.metrics_service import collect_and_store_metrics, get_all_metrics

router = APIRouter()



def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/collect")
def collect_metrics(db:Session = Depends(get_db)):
    return collect_and_store_metrics(db)

@router.get("/metrics")
def read_metrics(db: Session =Depends(get_db)):
    data = get_all_metrics(db)
    return [{"id":item.id,
             "cpu_usage":item.cpu_usage,
             "memory_usage":item.memory_usage,
             "request_load":item.request_load,
             "timestamp":item.timestamp,}
             
             for item in data]


