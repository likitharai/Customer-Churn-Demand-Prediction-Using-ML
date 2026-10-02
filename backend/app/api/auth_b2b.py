import hashlib
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.login_rate_limit import login_limiter
from app.core.security import clear_session_cookie, create_access_token, get_current_user, hash_password, set_session_cookie, verify_password
from app.database.model import User
from app.database.saas_models import Invitation, Membership, Organization
from app.database.session import get_db
from app.schemas.auth import LoginRequest, SessionResponse, UserResponse

router = APIRouter()


class AcceptInvitationRequest(BaseModel):
    token: str = Field(min_length=20)
    full_name: str = Field(min_length=2, max_length=120)
    password: str = Field(min_length=12, max_length=128)


def invitation(db, token):
    row = db.query(Invitation).filter_by(token_hash=hashlib.sha256(token.encode()).hexdigest()).first()
    if not row or row.accepted_at or row.expires_at < datetime.utcnow():
        raise HTTPException(400, "Invitation is invalid or expired")
    return row


@router.post("/login", response_model=SessionResponse)
def login(payload: LoginRequest, request: Request, response: Response, db: Session = Depends(get_db)):
    key = f"{request.client.host if request.client else 'unknown'}:{payload.email.lower()}"
    login_limiter.check(key)
    user = db.query(User).filter_by(email=payload.email.lower()).first()
    if not user or not verify_password(payload.password, user.password_hash):
        login_limiter.failure(key)
        raise HTTPException(401, "Invalid email or password")
    if not user.is_active:
        login_limiter.failure(key)
        raise HTTPException(403, "Account is disabled")
    membership = db.query(Membership).filter_by(user_id=user.id).first()
    if not membership:
        raise HTTPException(403, "This account has not been invited to a workspace. Contact your administrator.")
    if user.role != membership.role:
        user.role = membership.role
        db.commit()
        db.refresh(user)
    login_limiter.success(key)
    set_session_cookie(response, create_access_token(user))
    return {"user": user}


@router.get("/invitation/{token}")
def invitation_details(token: str, db: Session = Depends(get_db)):
    row = invitation(db, token)
    organization = db.get(Organization, row.organization_id)
    return {"email": row.email, "role": row.role, "organization": organization.name, "expires_at": row.expires_at}


@router.post("/accept-invitation", response_model=SessionResponse, status_code=201)
def accept(payload: AcceptInvitationRequest, response: Response, db: Session = Depends(get_db)):
    row = invitation(db, payload.token)
    if db.query(User).filter_by(email=row.email).first():
        raise HTTPException(409, "An account already exists for this email. Sign in and ask the administrator to reassign it.")
    user = User(email=row.email, full_name=payload.full_name.strip(), company=None, password_hash=hash_password(payload.password), role=row.role)
    db.add(user)
    db.flush()
    db.add(Membership(organization_id=row.organization_id, user_id=user.id, role=row.role))
    row.accepted_at = datetime.utcnow()
    db.commit()
    db.refresh(user)
    set_session_cookie(response, create_access_token(user))
    return {"user": user}


@router.get("/me", response_model=UserResponse)
def me(user: User = Depends(get_current_user)):
    return user


@router.post("/logout", status_code=204)
def logout(response: Response):
    clear_session_cookie(response)
    return None
