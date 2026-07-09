from fastapi import APIRouter, HTTPException
from app.services.recommendation_service import RecommendationService

router = APIRouter()
service = RecommendationService()

@router.post("/generate")
def generate_recommendations(customer: dict):
    try:
        return service.generate(customer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
