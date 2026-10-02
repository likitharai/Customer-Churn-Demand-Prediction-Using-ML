from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.core.tenancy import audit, require_manager, tenant_context
from app.database.interaction_model import TenantInteraction
from app.database.model import Customer, User
from app.database.saas_models import Membership, OrganizationCustomer, PredictionRecord, RetentionOutcome, RetentionTask


router = APIRouter()


class WorkflowInteractionInput(BaseModel):
    customer_id: str = Field(min_length=2, max_length=20)
    channel: str = Field(pattern="^(email|phone|chat|meeting)$")
    subject: str = Field(min_length=2, max_length=160)
    notes: str | None = None
    sentiment: str = Field(pattern="^(positive|neutral|negative)$")
    problem_category: str = Field(pattern="^(price|service|competitor|features|billing|contract|other)$")
    cancellation_intent: str = Field(pattern="^(none|low|medium|high)$")
    requested_solution: str | None = None
    reaction: str = Field(pattern="^(negative|neutral|interested|positive)$")
    follow_up_required: bool = True
    follow_up_at: datetime | None = None


class ResolveFollowUpInput(BaseModel):
    customer_response: str = Field(pattern="^(offer_accepted|offer_rejected|needs_time|issue_resolved|customer_retained|still_cancelling|customer_churned)$")
    offer_type: str | None = Field(default=None, max_length=100)
    offer_cost: float = Field(default=0, ge=0)
    offer_duration: str | None = Field(default=None, max_length=80)
    final_sentiment: str = Field(pattern="^(positive|neutral|negative)$")
    notes: str | None = None
    next_follow_up_at: datetime | None = None


class ManualFollowUpInput(BaseModel):
    customer_id: str = Field(min_length=2, max_length=20)
    assigned_user_id: int
    title: str = Field(min_length=2, max_length=180)
    description: str | None = None
    priority: str = Field(pattern="^(low|medium|high|urgent)$")
    due_at: datetime | None = None

RECOMMENDATIONS = {
    "price": "Offer a right-sized plan or a time-bound loyalty discount.",
    "service": "Schedule a technical review and consider a service credit after resolution.",
    "competitor": "Compare the competitor offer and present the strongest approved match.",
    "features": "Recommend the most relevant feature bundle or product education session.",
    "billing": "Review the bill, correct errors, and explain recurring charges clearly.",
    "contract": "Offer a suitable renewal term with a transparent commitment benefit.",
    "other": "Clarify the root cause and agree on a specific next action with the customer.",
}

RESPONSE_ADJUSTMENTS = {
    "offer_accepted": -0.20,
    "offer_rejected": 0.10,
    "needs_time": 0.02,
    "issue_resolved": -0.15,
    "customer_retained": -0.30,
    "still_cancelling": 0.15,
    "customer_churned": 0.30,
}


def serialize(row):
    return {column.name: getattr(row, column.name) for column in row.__table__.columns}


def clamp(value):
    return round(max(0.01, min(0.99, float(value))), 4)


def ensure_customer_access(context, customer_id):
    db = context["db"]
    link = db.query(OrganizationCustomer).filter_by(
        organization_id=context["organization"].id,
        customer_id=customer_id,
    ).first()
    if not link:
        raise HTTPException(404, "Customer not found in this workspace")
    if context["membership"].role == "agent" and link.assigned_user_id != context["user"].id:
        raise HTTPException(403, "This customer is assigned to another employee")
    return link


def latest_prediction(db, organization_id, customer_id):
    return db.query(PredictionRecord).filter_by(
        organization_id=organization_id,
        customer_id=customer_id,
    ).order_by(PredictionRecord.predicted_at.desc()).first()


def interaction_adjustment(payload):
    adjustment = {"negative": 0.08, "neutral": 0, "positive": -0.05}[payload.sentiment]
    adjustment += {"none": 0, "low": 0.02, "medium": 0.06, "high": 0.12}[payload.cancellation_intent]
    adjustment += {"negative": 0.06, "neutral": 0, "interested": -0.03, "positive": -0.06}[payload.reaction]
    return adjustment


def task_payload(task, interaction=None):
    result = serialize(task)
    result["interaction"] = serialize(interaction) if interaction else None
    return result


@router.get("/workflow/interactions")
def list_interactions(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    context=Depends(tenant_context),
):
    db = context["db"]
    query = db.query(TenantInteraction).filter_by(organization_id=context["organization"].id)
    if context["membership"].role == "agent":
        query = query.filter(TenantInteraction.user_id == context["user"].id)
    total = query.count()
    rows = query.order_by(TenantInteraction.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    result = []
    for row in rows:
        item = serialize(row)
        task = db.query(RetentionTask).filter_by(organization_id=context["organization"].id, interaction_id=row.id).order_by(RetentionTask.created_at.desc()).first()
        item["follow_up"] = serialize(task) if task else None
        result.append(item)
    return {"items": result, "total": total, "page": page, "page_size": page_size, "pages": max(1, (total + page_size - 1) // page_size)}

@router.post("/workflow/interactions", status_code=201)
def create_interaction(payload: WorkflowInteractionInput, context=Depends(tenant_context)):
    db = context["db"]
    organization_id = context["organization"].id
    user = context["user"]
    link = ensure_customer_access(context, payload.customer_id)
    prediction = latest_prediction(db, organization_id, payload.customer_id)
    base_probability = float(prediction.probability if prediction else 0)
    operational_probability = clamp(base_probability + interaction_adjustment(payload))
    interaction = TenantInteraction(
        organization_id=organization_id,
        user_id=user.id,
        customer_id=payload.customer_id,
        channel=payload.channel,
        subject=payload.subject,
        notes=payload.notes,
        sentiment=payload.sentiment,
        status="follow-up" if payload.follow_up_required else "resolved",
        follow_up_at=payload.follow_up_at,
        problem_category=payload.problem_category,
        cancellation_intent=payload.cancellation_intent,
        requested_solution=payload.requested_solution,
        reaction=payload.reaction,
        follow_up_required=payload.follow_up_required,
        base_probability=base_probability,
        operational_probability=operational_probability,
    )
    db.add(interaction)
    db.flush()
    task = None
    if payload.follow_up_required:
        assigned_user_id = link.assigned_user_id or user.id
        task = RetentionTask(
            organization_id=organization_id,
            customer_id=payload.customer_id,
            interaction_id=interaction.id,
            assigned_user_id=assigned_user_id,
            created_by=user.id,
            title=f"Follow up: {payload.problem_category} concern",
            description=RECOMMENDATIONS[payload.problem_category],
            suggested_action=RECOMMENDATIONS[payload.problem_category],
            priority="urgent" if payload.cancellation_intent == "high" else "high" if payload.sentiment == "negative" else "medium",
            status="open",
            due_at=payload.follow_up_at or datetime.utcnow() + timedelta(days=1),
        )
        db.add(task)
        db.flush()
    audit(db, user, organization_id, "interaction.created_with_follow_up", "interaction", interaction.id, {
        "customer_id": payload.customer_id,
        "task_id": task.id if task else None,
        "base_probability": base_probability,
        "operational_probability": operational_probability,
    })
    db.commit()
    db.refresh(interaction)
    return {"interaction": serialize(interaction), "follow_up": serialize(task) if task else None}


@router.post("/workflow/tasks", status_code=201)
def create_manager_follow_up(payload: ManualFollowUpInput, context=Depends(require_manager)):
    db = context["db"]
    organization_id = context["organization"].id
    link = ensure_customer_access(context, payload.customer_id)
    membership = db.query(Membership).filter_by(
        organization_id=organization_id,
        user_id=payload.assigned_user_id,
        role="agent",
    ).first()
    agent = db.get(User, payload.assigned_user_id)
    if not membership or not agent or not agent.is_active:
        raise HTTPException(422, "Select an active Agent from this workspace")
    link.assigned_user_id = agent.id
    task = RetentionTask(
        organization_id=organization_id,
        customer_id=payload.customer_id,
        assigned_user_id=agent.id,
        created_by=context["user"].id,
        title=payload.title,
        description=payload.description,
        suggested_action=payload.description,
        priority=payload.priority,
        status="open",
        due_at=payload.due_at or datetime.utcnow() + timedelta(days=1),
    )
    db.add(task)
    db.flush()
    audit(db, context["user"], organization_id, "manager_follow_up.assigned", "task", task.id, {
        "customer_id": payload.customer_id,
        "assigned_user_id": agent.id,
    })
    db.commit()
    db.refresh(task)
    result = serialize(task)
    result["assigned_to"] = {"id": agent.id, "full_name": agent.full_name, "email": agent.email}
    return result

@router.get("/workflow/tasks")
def list_follow_ups(context=Depends(tenant_context)):
    db = context["db"]
    query = db.query(RetentionTask).filter_by(organization_id=context["organization"].id)
    if context["membership"].role == "agent":
        query = query.filter(RetentionTask.assigned_user_id == context["user"].id)
    rows = query.order_by(RetentionTask.completed_at.asc(), RetentionTask.due_at.asc()).all()
    result = []
    for row in rows:
        interaction = db.get(TenantInteraction, row.interaction_id) if row.interaction_id else None
        item = task_payload(row, interaction)
        assignee = db.get(User, row.assigned_user_id) if row.assigned_user_id else None
        item["assigned_to"] = {"id": assignee.id, "full_name": assignee.full_name, "email": assignee.email} if assignee else None
        result.append(item)
    return result


@router.post("/workflow/tasks/{task_id}/resolve")
def resolve_follow_up(task_id: int, payload: ResolveFollowUpInput, context=Depends(tenant_context)):
    db = context["db"]
    organization_id = context["organization"].id
    user = context["user"]
    task = db.query(RetentionTask).filter_by(id=task_id, organization_id=organization_id).first()
    if not task:
        raise HTTPException(404, "Follow-up not found")
    ensure_customer_access(context, task.customer_id)
    if context["membership"].role == "agent" and task.assigned_user_id != user.id:
        raise HTTPException(403, "This follow-up is assigned to another employee")
    interaction = db.get(TenantInteraction, task.interaction_id) if task.interaction_id else None
    prediction = latest_prediction(db, organization_id, task.customer_id)
    base_probability = float(interaction.operational_probability if interaction and interaction.operational_probability is not None else prediction.probability if prediction else 0)
    sentiment_adjustment = {"positive": -0.05, "neutral": 0, "negative": 0.05}[payload.final_sentiment]
    operational_probability = clamp(base_probability + RESPONSE_ADJUSTMENTS[payload.customer_response] + sentiment_adjustment)
    customer = db.get(Customer, task.customer_id)
    annual_revenue = float(customer.monthly_charges or 0) * 12
    protected_revenue = round(max(0, annual_revenue * (base_probability - operational_probability)), 2)
    expected_net_value = round(protected_revenue - payload.offer_cost, 2)
    retained = payload.customer_response in {"offer_accepted", "issue_resolved", "customer_retained"}
    outcome = RetentionOutcome(
        organization_id=organization_id,
        customer_id=task.customer_id,
        task_id=task.id,
        interaction_id=task.interaction_id,
        recorded_by=user.id,
        outcome="retained" if retained else "churned" if payload.customer_response == "customer_churned" else "pending",
        customer_response=payload.customer_response,
        offer_type=payload.offer_type,
        offer_cost=payload.offer_cost,
        offer_duration=payload.offer_duration,
        final_sentiment=payload.final_sentiment,
        base_probability=base_probability,
        operational_probability=operational_probability,
        revenue_protected=protected_revenue,
        expected_net_value=expected_net_value,
        notes=payload.notes,
    )
    db.add(outcome)
    task.status = "completed" if payload.customer_response not in {"needs_time", "still_cancelling"} else "follow-up"
    task.completed_at = datetime.utcnow() if task.status == "completed" else None
    task.offer_type = payload.offer_type
    task.offer_cost = payload.offer_cost
    task.offer_duration = payload.offer_duration
    if interaction:
        interaction.status = "resolved" if task.status == "completed" else "follow-up"
    if payload.next_follow_up_at and task.status != "completed":
        task.due_at = payload.next_follow_up_at
    audit(db, user, organization_id, "follow_up.resolved", "task", task.id, {
        "customer_response": payload.customer_response,
        "operational_probability": operational_probability,
        "revenue_protected": protected_revenue,
        "expected_net_value": expected_net_value,
    })
    db.commit()
    db.refresh(outcome)
    return {"task": serialize(task), "outcome": serialize(outcome)}


