from fastapi import APIRouter, HTTPException
from app.schemas.prediction import CustomerInput, PredictionResponse
from app.services.prediction_service import PredictionService

router = APIRouter()
service = PredictionService()

@router.post("/predict", response_model=PredictionResponse)
def predict(customer: CustomerInput):
    try:
        return service.predict(customer.dict())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/saved")
def get_saved_predictions():
    return service.get_saved_predictions()
