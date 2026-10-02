from fastapi import APIRouter, Depends

from app.api.imports_v2 import score_customers
from app.core.tenancy import audit, require_manager
from app.database.model import Customer
from app.database.saas_models import OrganizationCustomer


router = APIRouter()


@router.post("/imports/score-all")
def score_all_customers(context=Depends(require_manager)):
    db = context["db"]
    organization_id = context["organization"].id
    user = context["user"]
    customers = (
        db.query(Customer)
        .join(OrganizationCustomer, OrganizationCustomer.customer_id == Customer.customer_id)
        .filter(OrganizationCustomer.organization_id == organization_id)
        .all()
    )
    scored, failures = score_customers(db, organization_id, user.id, customers)
    audit(db, user, organization_id, "customers.bulk_scored", "organization", organization_id, {
        "predictions_created": scored,
        "scoring_errors": len(failures),
    })
    db.commit()
    return {"predictions_created": scored, "scoring_errors": len(failures), "errors": failures[:20]}
