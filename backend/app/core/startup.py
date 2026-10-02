import json
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.config import validate_environment
from app.core.security import hash_password
from app.database import saas_models
from app.database.interaction_model import TenantInteraction
from app.database.model import Customer, User
from app.database.saas_models import Membership, ModelVersion, Organization, OrganizationCustomer, RetentionPlaybook
from app.database.session import Base, SessionLocal, engine
from app.database.migration_runner import run_migrations


@asynccontextmanager
async def lifespan(_: FastAPI):
    validate_environment()
    Base.metadata.create_all(bind=engine)
    run_migrations()
    db = SessionLocal()
    try:
        email = os.getenv("ADMIN_EMAIL", "likitharai22@gmail.com").lower()
        user = db.query(User).filter_by(email=email).first()
        if not user and email != "admin@example.com":
            legacy = db.query(User).filter_by(email="admin@example.com", role="admin").first()
            if legacy:
                legacy.email = email
                user = legacy
        if not user:
            user = User(
                email=email,
                full_name="Platform Admin",
                role="admin",
                company="RetainIQ",
                password_hash=hash_password(os.getenv("ADMIN_PASSWORD", "ChangeMe123!")),
            )
            db.add(user)
            db.flush()
        org = db.query(Organization).filter_by(slug="retainiq-demo").first()
        if not org:
            org = Organization(name="RetainIQ Demo", slug="retainiq-demo", plan="growth")
            db.add(org)
            db.flush()
        if not db.query(Membership).filter_by(user_id=user.id).first():
            db.add(Membership(organization_id=org.id, user_id=user.id, role="admin"))
        sample = db.get(Customer, "SAMPLE-001")
        if sample and not db.query(OrganizationCustomer).filter_by(organization_id=org.id, customer_id=sample.customer_id).first():
            db.add(OrganizationCustomer(organization_id=org.id, customer_id=sample.customer_id, assigned_user_id=user.id))
        playbooks = [
            ("High-risk save", "High", "Call within 24 hours, diagnose the primary issue, and offer an annual-plan incentive."),
            ("Service recovery", "Medium", "Schedule a technical support review and confirm resolution within 48 hours."),
            ("Value expansion", "Low", "Share product adoption guidance and explore a relevant service upgrade."),
        ]
        for name, risk, action in playbooks:
            if not db.query(RetentionPlaybook).filter_by(organization_id=org.id, name=name).first():
                db.add(RetentionPlaybook(organization_id=org.id, name=name, trigger_risk=risk, recommended_action=action))
        if not db.query(ModelVersion).filter_by(version="v1.0.0").first():
            db.add(ModelVersion(version="v1.0.0", status="active", metrics_json=json.dumps({"accuracy": 0.7522, "roc_auc": 0.8257, "model_name": "LightGBM"}), artifact_path="model_pipeline.pkl"))
        db.commit()
    finally:
        db.close()
    yield



