import hashlib
import os
import secrets
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field, field_validator

from app.core.tenancy import audit, require_org_admin
from app.database.saas_models import Invitation
from app.services.email_service import send_invitation_email


router = APIRouter()


class InviteEmployee(BaseModel):
    email: str = Field(min_length=5, max_length=255)
    role: str = Field(pattern="^(agent|manager|admin)$")

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        normalized = value.strip().lower()
        if "@" not in normalized or normalized.startswith("@") or normalized.endswith("@"):
            raise ValueError("Enter a valid work email")
        return normalized


@router.post("/invitations", status_code=201)
def invite_employee(payload: InviteEmployee, context=Depends(require_org_admin)):
    db = context["db"]
    user = context["user"]
    organization = context["organization"]
    token = secrets.token_urlsafe(32)
    expires_at = datetime.utcnow() + timedelta(days=7)
    record = Invitation(
        organization_id=organization.id,
        email=payload.email,
        role=payload.role,
        token_hash=hashlib.sha256(token.encode()).hexdigest(),
        invited_by=user.id,
        expires_at=expires_at,
    )
    db.add(record)
    db.flush()
    base_url = os.getenv("APP_BASE_URL", "http://localhost:3000").rstrip("/")
    invitation_url = f"{base_url}/login?invite={token}"
    delivery = send_invitation_email(record.email, organization.name, record.role, invitation_url)
    audit(db, user, organization.id, "invitation.created", "invitation", record.id, {
        "email": record.email,
        "role": record.role,
        "email_delivery": delivery["status"],
    })
    db.commit()
    return {
        "invitation_id": record.id,
        "token": token,
        "invitation_url": invitation_url,
        "expires_at": expires_at,
        "email_delivery": delivery,
    }
