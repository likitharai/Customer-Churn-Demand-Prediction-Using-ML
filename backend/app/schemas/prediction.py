from pydantic import BaseModel
from typing import Optional


class CustomerInput(BaseModel):
    gender: Optional[str] = "Male"
    SeniorCitizen: Optional[int] = 0
    Partner: Optional[str] = "No"
    Dependents: Optional[str] = "No"
    tenure: Optional[float] = 12
    PhoneService: Optional[str] = "Yes"
    MultipleLines: Optional[str] = "No"
    InternetService: Optional[str] = "Fiber optic"
    OnlineSecurity: Optional[str] = "No"
    OnlineBackup: Optional[str] = "No"
    DeviceProtection: Optional[str] = "No"
    TechSupport: Optional[str] = "No"
    StreamingTV: Optional[str] = "No"
    StreamingMovies: Optional[str] = "No"
    Contract: Optional[str] = "Month-to-month"
    PaperlessBilling: Optional[str] = "Yes"
    PaymentMethod: Optional[str] = "Electronic check"
    MonthlyCharges: Optional[float] = 70.0
    TotalCharges: Optional[float] = 840.0


class PredictionResponse(BaseModel):
    prediction: int
    prediction_label: str
    probability: float
    risk_level: str