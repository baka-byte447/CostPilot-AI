from fastapi import FastAPI
from app.api.metrics import router as metrics_router
from app.config.database import engine, Base


from threading import Thread
from app.workers.metrics_collector import start_scheduler
app = FastAPI()

Base.metadata.create_all(bind=engine)
app.include_router(metrics_router)

@app.on_event("startup")
def start_background_worker():
    thread = Thread(target=start_scheduler)
    thread.daemon = True
    thread.start()