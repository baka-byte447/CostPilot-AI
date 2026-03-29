import schedule
import time
from sqlalchemy.orm import Session

from app.config.database import SessionLocal
from app.services.metrics_service import collect_and_store_metrics

def job():
    db: Session = SessionLocal()
    try:
        result = collect_and_store_metrics(db)
        print("Collected metrics: ",result)

    except Exception as e:
        print("Error collecting metrics: ",e)

    finally:
        db.close()


def start_scheduler():
    schedule.every(10).seconds.do(job)
    while(True):
        schedule.run_pending()
        time.sleep(1)

