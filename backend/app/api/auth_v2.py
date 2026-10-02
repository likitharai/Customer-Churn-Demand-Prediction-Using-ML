import re
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.security import create_access_token, get_current_user, hash_password, verify_password
from app.database.model import User
from app.database.saas_models import Membership, Organization
from app.database.session import get_db
from app.schemas.auth import AuthResponse, LoginRequest, RegisterRequest, UserResponse
router=APIRouter()

def slugify(value): return re.sub(r"[^a-z0-9]+","-",value.lower()).strip("-")[:60] or "workspace"
@router.post("/register",response_model=AuthResponse,status_code=201)
def register(payload:RegisterRequest,db:Session=Depends(get_db)):
    email=payload.email.lower()
    if db.query(User).filter_by(email=email).first(): raise HTTPException(409,"An account with this email already exists")
    user=User(email=email,full_name=payload.full_name.strip(),company=payload.company,password_hash=hash_password(payload.password),role="admin");db.add(user);db.flush()
    base=slugify(payload.company or payload.full_name);slug=base;counter=1
    while db.query(Organization).filter_by(slug=slug).first(): counter+=1;slug=f"{base}-{counter}"
    org=Organization(name=payload.company or f"{payload.full_name}'s workspace",slug=slug);db.add(org);db.flush();db.add(Membership(organization_id=org.id,user_id=user.id,role="admin"));db.commit();db.refresh(user)
    return AuthResponse(access_token=create_access_token(user),user=user)
@router.post("/login",response_model=AuthResponse)
def login(payload:LoginRequest,db:Session=Depends(get_db)):
    user=db.query(User).filter_by(email=payload.email.lower()).first()
    if not user or not verify_password(payload.password,user.password_hash): raise HTTPException(401,"Invalid email or password")
    if not user.is_active: raise HTTPException(403,"Account is disabled")
    membership=db.query(Membership).filter_by(user_id=user.id).first()
    if membership and user.role!=membership.role: user.role=membership.role;db.commit();db.refresh(user)
    return AuthResponse(access_token=create_access_token(user),user=user)
@router.get("/me",response_model=UserResponse)
def me(user:User=Depends(get_current_user)): return user
@router.post("/logout",status_code=204)
def logout(_:User=Depends(get_current_user)): return None
