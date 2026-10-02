from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text

from app.database.session import Base


class TenantInteraction(Base):
    __tablename__ = "tenant_interactions"
    id = Column(Integer, primary_key=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    customer_id = Column(String(20), index=True)
    channel = Column(String(30), nullable=False)
    subject = Column(String(160), nullable=False)
    notes = Column(Text)
    sentiment = Column(String(20), nullable=False, default="neutral")
    status = Column(String(30), nullable=False, default="open")
    follow_up_at = Column(DateTime)
    problem_category = Column(String(40))
    cancellation_intent = Column(String(20), nullable=False, default="none")
    requested_solution = Column(Text)
    reaction = Column(String(30), nullable=False, default="neutral")
    follow_up_required = Column(Boolean, nullable=False, default=False)
    base_probability = Column(Float)
    operational_probability = Column(Float)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
