from pathlib import Path
import os
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database.session import get_db

router = APIRouter()

ROOT_DIR = Path(__file__).resolve().parents[3]
MODEL_PATH = ROOT_DIR / "model_pipeline.pkl"


@router.get("/")
def health_check():
    return {
        "status": "healthy",
        "service": "RetainIQ Decision Intelligence Platform",
        "version": "3.4.0",
        "model_loaded": MODEL_PATH.exists(),
        "model_version": os.getenv("MODEL_VERSION", "v1.0.0"),
    }

@router.get("/db-check")
def db_check(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {"status": "database connected"}