from fastapi import APIRouter
from app.services.shap_service import SHAPService

router = APIRouter()
service = SHAPService()

@router.post("/explain")
def explain(customer: dict):
    return service.explain(customer)

@router.get("/feature-importance")
def feature_importance():
    return service.get_feature_importance()
