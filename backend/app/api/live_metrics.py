from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy import func

from app.core.tenancy import tenant_context
from app.database.model import Customer
from app.database.saas_models import OrganizationCustomer, PredictionRecord, RetentionOutcome, RetentionTask
from app.services.operational_risk import effective_probabilities, risk_level
from app.services.business_rules import revenue_at_risk


router = APIRouter()


@router.get("/metrics")
def metrics(context=Depends(tenant_context)):
    db = context["db"]
    organization_id = context["organization"].id
    user = context["user"]
    role = context["membership"].role
    links = db.query(OrganizationCustomer).filter_by(organization_id=organization_id)
    if role == "agent":
        links = links.filter_by(assigned_user_id=user.id)
    links = links.all()
    customer_ids = [link.customer_id for link in links]

    predictions = []
    if customer_ids:
        latest_ids = (
            db.query(func.max(PredictionRecord.id).label("prediction_id"))
            .filter(
                PredictionRecord.organization_id == organization_id,
                PredictionRecord.customer_id.in_(customer_ids),
            )
            .group_by(PredictionRecord.customer_id)
            .subquery()
        )
        predictions = db.query(PredictionRecord).join(
            latest_ids, PredictionRecord.id == latest_ids.c.prediction_id
        ).all()

    tasks = db.query(RetentionTask).filter(
        RetentionTask.organization_id == organization_id,
        RetentionTask.status != "completed",
    )
    if role == "agent":
        tasks = tasks.filter(RetentionTask.assigned_user_id == user.id)
    outcomes = db.query(RetentionOutcome).filter(
        RetentionOutcome.organization_id == organization_id,
        RetentionOutcome.customer_id.in_(customer_ids),
    ).all() if customer_ids else []
    retained = sum(item.outcome == "retained" for item in outcomes)
    effective = effective_probabilities(db, organization_id, customer_ids, {item.customer_id: item.probability for item in predictions})
    operational = [(item, *effective[item.customer_id]) for item in predictions]
    return {
        "scope": "assigned" if role == "agent" else "organization",
        "customers": len(links),
        "scored_customers": len(predictions),
        "high_risk": sum(risk_level(probability) in {"High", "Very High"} for _, probability, _ in operational),
        "revenue_at_risk": round(sum(revenue_at_risk(float(db.get(Customer, item.customer_id).monthly_charges or 0), probability) for item, probability, _ in operational), 2),
        "open_tasks": tasks.count(),
        "revenue_protected": round(sum(item.revenue_protected for item in outcomes), 2),
        "retention_success_rate": round(retained / len(outcomes) * 100, 1) if outcomes else 0,
        "refreshed_at": datetime.utcnow().isoformat(),
    }



