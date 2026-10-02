from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from app.database.session import Base

class Customer(Base):
    __tablename__ = "customers"

    customer_id = Column(String, primary_key=True, index=True)
    gender = Column(String, nullable=True)
    senior_citizen = Column(Integer, nullable=True)
    partner = Column(String, nullable=True)
    dependents = Column(String, nullable=True)
    tenure = Column(Integer, nullable=True)
    phone_service = Column(String, nullable=True)
    multiple_lines = Column(String, nullable=True)
    internet_service = Column(String, nullable=True)
    online_security = Column(String, nullable=True)
    online_backup = Column(String, nullable=True)
    device_protection = Column(String, nullable=True)
    tech_support = Column(String, nullable=True)
    streaming_tv = Column(String, nullable=True)
    streaming_movies = Column(String, nullable=True)
    contract = Column(String, nullable=True)
    paperless_billing = Column(String, nullable=True)
    payment_method = Column(String, nullable=True)
    monthly_charges = Column(Float, nullable=True)
    total_charges = Column(Float, nullable=True)
    churn = Column(String, nullable=True)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    full_name = Column(String(120), nullable=False)
    password_hash = Column(String(512), nullable=False)
    role = Column(String(20), nullable=False, default="customer")
    company = Column(String(120), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    interactions = relationship("CustomerInteraction", back_populates="owner")


class CustomerInteraction(Base):
    __tablename__ = "customer_interactions"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    customer_id = Column(String(20), nullable=True, index=True)
    channel = Column(String(30), nullable=False)
    subject = Column(String(160), nullable=False)
    notes = Column(Text, nullable=True)
    sentiment = Column(String(20), nullable=False, default="neutral")
    status = Column(String(20), nullable=False, default="open")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    owner = relationship("User", back_populates="interactions")
