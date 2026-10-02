from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from app.database.session import Base

class Organization(Base):
    __tablename__ = "organizations"
    id = Column(Integer, primary_key=True)
    name = Column(String(160), nullable=False)
    slug = Column(String(80), unique=True, nullable=False, index=True)
    plan = Column(String(30), nullable=False, default="starter")
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

class Membership(Base):
    __tablename__ = "memberships"
    __table_args__ = (UniqueConstraint("organization_id", "user_id"),)
    id = Column(Integer, primary_key=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(20), nullable=False, default="agent")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

class OrganizationCustomer(Base):
    __tablename__ = "organization_customers"
    __table_args__ = (UniqueConstraint("organization_id", "customer_id"),)
    id = Column(Integer, primary_key=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    customer_id = Column(String(20), ForeignKey("customers.customer_id", ondelete="CASCADE"), nullable=False, index=True)
    assigned_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    lifecycle_status = Column(String(30), nullable=False, default="active")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

class PredictionRecord(Base):
    __tablename__ = "prediction_records"
    id = Column(Integer, primary_key=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    customer_id = Column(String(20), nullable=False, index=True)
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    probability = Column(Float, nullable=False)
    risk_level = Column(String(20), nullable=False)
    prediction_label = Column(String(40), nullable=False)
    revenue_at_risk = Column(Float, nullable=False, default=0)
    model_version = Column(String(80), nullable=False, default="v2.0")
    explanation_json = Column(Text, nullable=True)
    predicted_at = Column(DateTime, nullable=False, default=datetime.utcnow)

class RetentionTask(Base):
    __tablename__ = "retention_tasks"
    id = Column(Integer, primary_key=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    customer_id = Column(String(20), nullable=True, index=True)
    interaction_id = Column(Integer, ForeignKey("tenant_interactions.id", ondelete="SET NULL"), nullable=True, index=True)
    assigned_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    title = Column(String(180), nullable=False)
    description = Column(Text, nullable=True)
    suggested_action = Column(Text, nullable=True)
    offer_type = Column(String(100), nullable=True)
    offer_cost = Column(Float, nullable=False, default=0)
    offer_duration = Column(String(80), nullable=True)
    priority = Column(String(20), nullable=False, default="medium")
    status = Column(String(30), nullable=False, default="open")
    due_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

class RetentionPlaybook(Base):
    __tablename__ = "retention_playbooks"
    id = Column(Integer, primary_key=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(160), nullable=False)
    description = Column(Text, nullable=True)
    trigger_risk = Column(String(20), nullable=False, default="High")
    recommended_action = Column(Text, nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
class RetentionOutcome(Base):
    __tablename__ = "retention_outcomes"
    id = Column(Integer, primary_key=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    customer_id = Column(String(20), nullable=False, index=True)
    task_id = Column(Integer, ForeignKey("retention_tasks.id", ondelete="SET NULL"), nullable=True, index=True)
    interaction_id = Column(Integer, ForeignKey("tenant_interactions.id", ondelete="SET NULL"), nullable=True, index=True)
    recorded_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    outcome = Column(String(40), nullable=False)
    customer_response = Column(String(40), nullable=True)
    offer_type = Column(String(100), nullable=True)
    offer_cost = Column(Float, nullable=False, default=0)
    offer_duration = Column(String(80), nullable=True)
    final_sentiment = Column(String(20), nullable=True)
    base_probability = Column(Float, nullable=True)
    operational_probability = Column(Float, nullable=True)
    revenue_protected = Column(Float, nullable=False, default=0)
    expected_net_value = Column(Float, nullable=False, default=0)
    notes = Column(Text, nullable=True)
    recorded_at = Column(DateTime, nullable=False, default=datetime.utcnow)
class Invitation(Base):
    __tablename__ = "invitations"
    id = Column(Integer, primary_key=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    email = Column(String(255), nullable=False, index=True)
    role = Column(String(20), nullable=False, default="agent")
    token_hash = Column(String(128), unique=True, nullable=False)
    invited_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    accepted_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

class DataImport(Base):
    __tablename__ = "data_imports"
    id = Column(Integer, primary_key=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    uploaded_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    filename = Column(String(255), nullable=False)
    row_count = Column(Integer, nullable=False, default=0)
    status = Column(String(30), nullable=False, default="completed")
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

class ModelVersion(Base):
    __tablename__ = "model_versions"
    id = Column(Integer, primary_key=True)
    version = Column(String(80), unique=True, nullable=False)
    status = Column(String(30), nullable=False, default="active")
    metrics_json = Column(Text, nullable=True)
    artifact_path = Column(String(255), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    action = Column(String(100), nullable=False)
    entity_type = Column(String(80), nullable=True)
    entity_id = Column(String(80), nullable=True)
    details_json = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)



