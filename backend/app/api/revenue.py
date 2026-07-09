from fastapi import APIRouter
from app.services.revenue_service import RevenueService

router = APIRouter()
service = RevenueService()

@router.get("/summary")
def revenue_summary():
    return service.get_revenue_risk_summary()

@router.get("/high-risk")
def high_risk_customers():
    return service.get_high_risk_customers()
