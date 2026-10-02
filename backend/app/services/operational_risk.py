from app.database.interaction_model import TenantInteraction
from app.database.saas_models import RetentionOutcome
from app.services.business_rules import risk_level


def effective_probabilities(db, organization_id, customer_ids, ml_probabilities=None):
    ml_probabilities = ml_probabilities or {}
    result = {customer_id: (float(ml_probabilities.get(customer_id, 0) or 0), "ml") for customer_id in customer_ids}
    latest = {}
    if not customer_ids:
        return result
    interactions = db.query(TenantInteraction).filter(
        TenantInteraction.organization_id == organization_id,
        TenantInteraction.customer_id.in_(customer_ids),
        TenantInteraction.operational_probability.isnot(None),
    ).order_by(TenantInteraction.created_at.desc()).all()
    for item in interactions:
        current = latest.get(item.customer_id)
        if current is None or item.created_at > current[0]:
            latest[item.customer_id] = (item.created_at, float(item.operational_probability), "interaction")
    outcomes = db.query(RetentionOutcome).filter(
        RetentionOutcome.organization_id == organization_id,
        RetentionOutcome.customer_id.in_(customer_ids),
        RetentionOutcome.operational_probability.isnot(None),
    ).order_by(RetentionOutcome.recorded_at.desc()).all()
    for item in outcomes:
        current = latest.get(item.customer_id)
        if current is None or item.recorded_at > current[0]:
            latest[item.customer_id] = (item.recorded_at, float(item.operational_probability), "outcome")
    for customer_id, (_, probability, source) in latest.items():
        result[customer_id] = (probability, source)
    return result


def effective_probability(db, organization_id, customer_id, ml_probability=0):
    return effective_probabilities(db, organization_id, [customer_id], {customer_id: ml_probability})[customer_id]
