from fastapi import APIRouter, Depends
from sqlalchemy import func

from app.core.tenancy import require_manager, tenant_context
from app.database.interaction_model import TenantInteraction
from app.database.model import Customer, User
from app.database.saas_models import Membership, OrganizationCustomer, PredictionRecord, RetentionTask
from app.services.operational_risk import effective_probabilities, risk_level
from app.services.business_rules import revenue_at_risk


router = APIRouter()


@router.get("/risk-queue")
def risk_queue(context=Depends(tenant_context)):
    db = context["db"]
    organization_id = context["organization"].id
    latest = (
        db.query(
            PredictionRecord.customer_id.label("customer_id"),
            func.max(PredictionRecord.id).label("prediction_id"),
        )
        .filter(PredictionRecord.organization_id == organization_id)
        .group_by(PredictionRecord.customer_id)
        .subquery()
    )
    query = (
        db.query(OrganizationCustomer, Customer, PredictionRecord)
        .join(Customer, Customer.customer_id == OrganizationCustomer.customer_id)
        .outerjoin(latest, latest.c.customer_id == OrganizationCustomer.customer_id)
        .outerjoin(PredictionRecord, PredictionRecord.id == latest.c.prediction_id)
        .filter(OrganizationCustomer.organization_id == organization_id)
    )
    if context["membership"].role == "agent":
        query = query.filter(OrganizationCustomer.assigned_user_id == context["user"].id)
    rows = query.all()
    ml_probabilities = {customer.customer_id: float(prediction.probability if prediction else 0) for _, customer, prediction in rows}
    operational = effective_probabilities(db, organization_id, list(ml_probabilities), ml_probabilities)
    result = []
    for link, customer, prediction in rows:
        ml_probability = ml_probabilities[customer.customer_id]
        probability, source = operational[customer.customer_id]
        monthly_charges = float(customer.monthly_charges or 0)
        result.append({
            "customer_id": customer.customer_id,
            "monthly_charges": monthly_charges,
            "contract": customer.contract,
            "assigned_user_id": link.assigned_user_id,
            "risk_level": risk_level(probability) if prediction else "Unscored",
            "probability": probability,
            "ml_probability": ml_probability,
            "risk_source": source,
            "revenue_at_risk": round(revenue_at_risk(monthly_charges, probability), 2),
            "priority_score": round(probability * monthly_charges * 12, 2),
        })
    return sorted(result, key=lambda item: item["priority_score"], reverse=True)

@router.get("/manager-analytics")
def manager_analytics(context=Depends(require_manager)):
    db = context["db"]
    organization_id = context["organization"].id
    members = []
    rows = (
        db.query(Membership, User)
        .join(User, User.id == Membership.user_id)
        .filter(Membership.organization_id == organization_id)
        .all()
    )
    for membership, user in rows:
        assigned = db.query(OrganizationCustomer).filter_by(
            organization_id=organization_id, assigned_user_id=user.id
        ).count()
        open_tasks = db.query(RetentionTask).filter(
            RetentionTask.organization_id == organization_id,
            RetentionTask.assigned_user_id == user.id,
            RetentionTask.status != "completed",
        ).count()
        interactions = db.query(TenantInteraction).filter_by(
            organization_id=organization_id, user_id=user.id
        ).count()
        members.append({
            "id": user.id,
            "full_name": user.full_name,
            "email": user.email,
            "role": membership.role,
            "assigned_customers": assigned,
            "open_tasks": open_tasks,
            "interactions": interactions,
        })
    return {
        "members": members,
        "total_interactions": sum(item["interactions"] for item in members),
        "unassigned_customers": db.query(OrganizationCustomer).filter_by(
            organization_id=organization_id, assigned_user_id=None
        ).count(),
    }



