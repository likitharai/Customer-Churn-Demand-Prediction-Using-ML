from fastapi import APIRouter
from app.services.revenue_service import RevenueService

router = APIRouter()
service = RevenueService()

@router.get("/kpis")
def get_kpis():
    return service.get_executive_kpis()

@router.get("/churn-by-segment")
def churn_by_segment():
    return service.get_churn_by_segment()
