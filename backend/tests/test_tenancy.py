"""Unit tests for multi-tenant isolation, membership validation, and role-based permissions."""

from __future__ import annotations

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.tenancy import (
    membership_for,
    require_manager,
    require_org_admin,
    tenant_context,
)
from app.database.interaction_model import TenantInteraction
from app.database.model import Base, Customer, User
from app.database.saas_models import Membership, Organization, OrganizationCustomer, PredictionRecord


@pytest.fixture
def in_memory_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


class TestMultiTenancyIsolation:
    def test_membership_and_inactive_org(self, in_memory_db):
        db = in_memory_db
        # Create active org and inactive org
        org_active = Organization(name="Acme Corp", slug="acme", is_active=True)
        org_inactive = Organization(name="Inactive Corp", slug="inactive", is_active=False)
        db.add_all([org_active, org_inactive])
        db.flush()

        user1 = User(id=1, email="user1@acme.com", full_name="User One", password_hash="pw")
        user2 = User(id=2, email="user2@inactive.com", full_name="User Two", password_hash="pw")
        user3 = User(id=3, email="user3@none.com", full_name="User Three", password_hash="pw")
        db.add_all([user1, user2, user3])
        db.flush()

        mem1 = Membership(user_id=user1.id, organization_id=org_active.id, role="agent")
        mem2 = Membership(user_id=user2.id, organization_id=org_inactive.id, role="manager")
        db.add_all([mem1, mem2])
        db.commit()

        # Valid active context
        ctx = tenant_context(db=db, user=user1)
        assert ctx["organization"].name == "Acme Corp"
        assert ctx["membership"].role == "agent"

        # Inactive org raises 403
        with pytest.raises(HTTPException) as exc_info:
            tenant_context(db=db, user=user2)
        assert exc_info.value.status_code == 403

        # User without membership raises 403
        with pytest.raises(HTTPException) as exc_info2:
            tenant_context(db=db, user=user3)
        assert exc_info2.value.status_code == 403

    def test_role_enforcement(self):
        agent_ctx = {"membership": Membership(role="agent")}
        manager_ctx = {"membership": Membership(role="manager")}
        admin_ctx = {"membership": Membership(role="admin")}

        # require_manager
        with pytest.raises(HTTPException) as exc:
            require_manager(agent_ctx)
        assert exc.value.status_code == 403

        assert require_manager(manager_ctx) == manager_ctx
        assert require_manager(admin_ctx) == admin_ctx

        # require_org_admin
        with pytest.raises(HTTPException) as exc2:
            require_org_admin(agent_ctx)
        assert exc2.value.status_code == 403

        with pytest.raises(HTTPException) as exc3:
            require_org_admin(manager_ctx)
        assert exc3.value.status_code == 403

        assert require_org_admin(admin_ctx) == admin_ctx

    def test_cross_tenant_data_isolation(self, in_memory_db):
        db = in_memory_db
        org_a = Organization(name="Tenant A", slug="tenant-a", is_active=True)
        org_b = Organization(name="Tenant B", slug="tenant-b", is_active=True)
        db.add_all([org_a, org_b])
        db.flush()

        cust_a = Customer(customer_id="CUST-A-001", monthly_charges=100.0, tenure=12)
        cust_b = Customer(customer_id="CUST-B-001", monthly_charges=50.0, tenure=24)
        db.add_all([cust_a, cust_b])
        db.flush()

        link_a = OrganizationCustomer(organization_id=org_a.id, customer_id="CUST-A-001")
        link_b = OrganizationCustomer(organization_id=org_b.id, customer_id="CUST-B-001")
        db.add_all([link_a, link_b])

        pred_a = PredictionRecord(
            organization_id=org_a.id,
            customer_id="CUST-A-001",
            probability=0.85,
            risk_level="Very High",
            prediction_label="Churn likely",
            revenue_at_risk=85.0,
            model_version="1.0.0",
        )
        pred_b = PredictionRecord(
            organization_id=org_b.id,
            customer_id="CUST-B-001",
            probability=0.20,
            risk_level="Low",
            prediction_label="Churn unlikely",
            revenue_at_risk=10.0,
            model_version="1.0.0",
        )
        db.add_all([pred_a, pred_b])
        db.commit()

        # Query customers for Org A
        org_a_customers = (
            db.query(OrganizationCustomer)
            .filter(OrganizationCustomer.organization_id == org_a.id)
            .all()
        )
        org_a_cust_ids = [c.customer_id for c in org_a_customers]
        assert "CUST-A-001" in org_a_cust_ids
        assert "CUST-B-001" not in org_a_cust_ids

        # Query predictions for Org B
        org_b_preds = (
            db.query(PredictionRecord)
            .filter(PredictionRecord.organization_id == org_b.id)
            .all()
        )
        assert len(org_b_preds) == 1
        assert org_b_preds[0].customer_id == "CUST-B-001"
        assert org_b_preds[0].probability == 0.20
