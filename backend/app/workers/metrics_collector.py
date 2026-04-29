import schedule
import time
from datetime import datetime
from threading import Lock
from sqlalchemy.orm import Session

from app.config.database import SessionLocal
from app.services.metrics_service import collect_and_store_metrics


_state_lock = Lock()
_scheduler_state = {
    "started_at": None,
    "last_run": None,
    "last_success": None,
    "last_error": None,
    "total_runs": 0,
    "successful_runs": 0,
}

_last_explanation = None


def _utc_now_iso() -> str:
    return datetime.utcnow().isoformat() + "Z"


def get_scheduler_state():
    with _state_lock:
        return dict(_scheduler_state)


def set_last_explanation(explanation):
    global _last_explanation
    with _state_lock:
        _last_explanation = explanation


def get_last_explanation():
    with _state_lock:
        return _last_explanation

def job():
    run_time = _utc_now_iso()

    with _state_lock:
        _scheduler_state["last_run"] = run_time
        _scheduler_state["total_runs"] += 1

    db: Session = SessionLocal()
    try:
        result = collect_and_store_metrics(db)

        with _state_lock:
            _scheduler_state["last_success"] = run_time
            _scheduler_state["last_error"] = None
            _scheduler_state["successful_runs"] += 1

        print("Collected metrics: ", result)

    except Exception as e:
        with _state_lock:
            _scheduler_state["last_error"] = str(e)

        print("Error collecting metrics: ", e)

    finally:
        db.close()


def start_scheduler():
    with _state_lock:
        _scheduler_state["started_at"] = _utc_now_iso()

    schedule.every(10).seconds.do(job)
    while True:
        schedule.run_pending()
        time.sleep(1)

