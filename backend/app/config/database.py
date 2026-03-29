from sqlalchemy import  create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URI = "sqlite:///./database/metrics.db"

engine = create_engine(DATABASE_URI,connect_args={"check_same_thread":False})

SessionLocal = sessionmaker(bind=engine)
Base= declarative_base()