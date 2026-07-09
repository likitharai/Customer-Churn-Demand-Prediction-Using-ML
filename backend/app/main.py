"""FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import prediction, analytics, recommendation, shap, revenue, health

app = FastAPI(
    title="Decision Intelligence Platform API",
    description="Customer Churn Prediction & Revenue Risk Analysis",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api/health", tags=["Health"])
app.include_router(prediction.router, prefix="/api/prediction", tags=["Prediction"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["Analytics"])
app.include_router(recommendation.router, prefix="/api/recommendation", tags=["Recommendation"])
app.include_router(shap.router, prefix="/api/shap", tags=["SHAP"])
app.include_router(revenue.router, prefix="/api/revenue", tags=["Revenue"])
