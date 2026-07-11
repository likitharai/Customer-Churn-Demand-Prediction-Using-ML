from fastapi import APIRouter
from app.services.shap_service import SHAPService

router = APIRouter()

@router.post("/explain")
def explain(customer: dict):
    service = SHAPService()
    return service.explain(customer)

@router.get("/feature-importance")
def feature_importance():
    service = SHAPService()
    return service.get_feature_importance()
