from fastapi import APIRouter, Depends

from app.core.tenancy import require_manager, tenant_context
from app.database.interaction_model import TenantInteraction
from app.database.model import Customer, User
from app.database.saas_models import Membership, OrganizationCustomer, PredictionRecord, RetentionTask


router = APIRouter()


def organization_id(context):
    return context["organization"].id


def customer_scope(context):
    query = context["db"].query(OrganizationCustomer).filter_by(
        organization_id=organization_id(context)
    )
    if context["membership"].role == "agent":
        query = query.filter(OrganizationCustomer.assigned_user_id == context["user"].id)
    return query


@router.get("/risk-queue")
def risk_queue(context=Depends(tenant_context)):
    db = context["db"]
    org_id = organization_id(context)
    result = []
    for link in customer_scope(context).all():
        customer = db.get(Customer, link.customer_id)
        prediction = (
            db.query(PredictionRecord)
            .filter_by(organization_id=org_id, customer_id=customer.customer_id)
            .order_by(PredictionRecord.predicted_at.desc())
            .first()
        )
        probability = prediction.probability if prediction else 0
        monthly_charges = float(customer.monthly_charges or 0)
        result.append(
            {
                "customer_id": customer.customer_id,
                "monthly_charges": monthly_charges,
                "contract": customer.contract,
                "assigned_user_id": link.assigned_user_id,
                "risk_level": prediction.risk_level if prediction else "Unscored",
                "probability": probability,
                "revenue_at_risk": prediction.revenue_at_risk if prediction else 0,
                "priority_score": round(probability * monthly_charges * 12, 2),
            }
        )
    return sorted(result, key=lambda item: item["priority_score"], reverse=True)


@router.get("/manager-analytics")
def manager_analytics(context=Depends(require_manager)):
    db = context["db"]
    org_id = organization_id(context)
    members = []
    rows = (
        db.query(Membership, User)
        .join(User, User.id == Membership.user_id)
        .filter(Membership.organization_id == org_id)
        .all()
    )
    for membership, user in rows:
        assigned = db.query(OrganizationCustomer).filter_by(
            organization_id=org_id, assigned_user_id=user.id
        ).count()
        open_tasks = db.query(RetentionTask).filter(
            RetentionTask.organization_id == org_id,
            RetentionTask.assigned_user_id == user.id,
            RetentionTask.status != "completed",
        ).count()
        interactions = db.query(TenantInteraction).filter_by(
            organization_id=org_id, user_id=user.id
        ).count()
        members.append(
            {
                "id": user.id,
                "full_name": user.full_name,
                "email": user.email,
                "role": membership.role,
                "assigned_customers": assigned,
                "open_tasks": open_tasks,
                "interactions": interactions,
            }
        )
    return {
        "members": members,
        "total_interactions": sum(item["interactions"] for item in members),
        "unassigned_customers": db.query(OrganizationCustomer).filter_by(
            organization_id=org_id, assigned_user_id=None
        ).count(),
    }
