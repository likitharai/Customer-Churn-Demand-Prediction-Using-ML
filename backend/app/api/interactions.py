from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.database.model import CustomerInteraction, User
from app.database.session import get_db
from app.schemas.interaction import InteractionCreate, InteractionResponse

router = APIRouter()


@router.get("/", response_model=list[InteractionResponse])
def list_interactions(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    query = db.query(CustomerInteraction)
    if user.role != "admin":
        query = query.filter(CustomerInteraction.user_id == user.id)
    return query.order_by(CustomerInteraction.created_at.desc()).limit(200).all()


@router.post("/", response_model=InteractionResponse, status_code=201)
def create_interaction(payload: InteractionCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    interaction = CustomerInteraction(user_id=user.id, **payload.model_dump())
    db.add(interaction)
    db.commit()
    db.refresh(interaction)
    return interaction
