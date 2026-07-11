from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database.session import get_db

router = APIRouter()

@router.get("/")
def health_check():
    return {"status": "ok", "service": "Decision Intelligence Platform"}

@router.get("/db-check")
def db_check(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {"status": "database connected"}