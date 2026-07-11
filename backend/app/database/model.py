from sqlalchemy import Column, Integer, String, Float
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