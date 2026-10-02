from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.security import require_admin
from app.database.model import Customer, CustomerInteraction, User
from app.database.session import get_db

router = APIRouter()


@router.get("/overview")
def overview(db: Session = Depends(get_db), _: User = Depends(require_admin)):
    total_users = db.query(func.count(User.id)).scalar() or 0
    active_users = db.query(func.count(User.id)).filter(User.is_active.is_(True)).scalar() or 0
    interactions = db.query(func.count(CustomerInteraction.id)).scalar() or 0
    open_items = db.query(func.count(CustomerInteraction.id)).filter(CustomerInteraction.status != "resolved").scalar() or 0
    customers = db.query(func.count(Customer.customer_id)).scalar() or 0
    return {"total_users": total_users, "active_users": active_users, "customers": customers,
            "interactions": interactions, "open_interactions": open_items}


@router.get("/users")
def users(db: Session = Depends(get_db), _: User = Depends(require_admin)):
    return [{"id": user.id, "email": user.email, "full_name": user.full_name, "role": user.role,
             "company": user.company, "is_active": user.is_active, "created_at": user.created_at}
            for user in db.query(User).order_by(User.created_at.desc()).all()]
