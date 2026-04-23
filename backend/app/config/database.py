from sqlalchemy import  create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

import os
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
db_path = os.path.join(BASE_DIR, "database", "metrics.db")
DATABASE_URI = f"sqlite:///{db_path}"

engine = create_engine(DATABASE_URI,connect_args={"check_same_thread":False})

SessionLocal = sessionmaker(bind=engine)
Base= declarative_base()