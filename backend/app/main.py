"""FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import prediction, analytics, recommendation,revenue, health, customer
from app.database.session import engine
from app.database.model import Base




Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Decision Intelligence Platform API",
    description="Customer Churn Prediction & Revenue Risk Analysis",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
@app.get("/")
def root():
    return {"message": "Decision Intelligence Platform API is running"}

app.include_router(health.router, prefix="/api/health", tags=["Health"])
app.include_router(prediction.router, prefix="/api/prediction", tags=["Prediction"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["Analytics"])
app.include_router(recommendation.router, prefix="/api/recommendation", tags=["Recommendation"])
app.include_router(revenue.router, prefix="/api/revenue", tags=["Revenue"])
app.include_router(customer.router, prefix="/api/customers", tags=["Customers"])

