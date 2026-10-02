import json
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.security import get_current_user
from app.database.model import User
from app.database.saas_models import AuditLog, Membership, Organization
from app.database.session import get_db

def membership_for(db: Session, user: User) -> Membership:
    membership = db.query(Membership).filter(Membership.user_id == user.id).first()
    if not membership: raise HTTPException(status_code=403, detail="No organization membership")
    return membership

def tenant_context(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    membership = membership_for(db, user)
    organization = db.get(Organization, membership.organization_id)
    if not organization or not organization.is_active: raise HTTPException(status_code=403, detail="Organization is inactive")
    return {"db": db, "user": user, "membership": membership, "organization": organization}

def require_manager(context=Depends(tenant_context)):
    if context["membership"].role not in {"manager", "admin"}: raise HTTPException(status_code=403, detail="Manager access required")
    return context

def require_org_admin(context=Depends(tenant_context)):
    if context["membership"].role != "admin": raise HTTPException(status_code=403, detail="Organization administrator access required")
    return context

def audit(db, user, organization_id, action, entity_type=None, entity_id=None, details=None):
    db.add(AuditLog(organization_id=organization_id, user_id=user.id, action=action, entity_type=entity_type, entity_id=str(entity_id) if entity_id else None, details_json=json.dumps(details or {})))
