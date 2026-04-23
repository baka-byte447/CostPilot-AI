from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.config.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    name = Column(String, nullable=True)
    company = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    subscription_plan = Column(String, default="free")

    credentials = relationship("UserCredential", back_populates="user", cascade="all, delete-orphan")


class UserCredential(Base):
    __tablename__ = "user_credentials"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    provider = Column(String, nullable=False)
    encrypted_credentials = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="credentials")

    __table_args__ = (
        __import__("sqlalchemy").UniqueConstraint("user_id", "provider", name="uq_user_provider"),
    )
