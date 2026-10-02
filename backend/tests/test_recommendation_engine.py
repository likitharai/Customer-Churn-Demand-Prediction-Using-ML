"""Unit tests for deterministic customer retention recommendation engine."""

from __future__ import annotations

import pytest
from app.services.recommendation_service import RecommendationEngine, RecommendationService


class TestRecommendationEngine:
    @pytest.fixture
    def engine(self):
        return RecommendationEngine()

    def test_high_risk_month_to_month_recommendations(self, engine):
        customer = {
            "probability": 0.75,
            "risk_level": "High",
            "Contract": "Month-to-month",
            "tenure": 6,
            "MonthlyCharges": 85.0,
            "InternetService": "Fiber optic",
            "TechSupport": "No",
        }
        recs = engine.recommend_for_row(customer)
        assert "Customer Success Call" in recs
        assert "Offer Discount" in recs
        assert "Upgrade Contract" in recs
        assert "Loyalty Program" in recs
        assert "Free Tech Support" in recs
        # Ensure no duplicates
        assert len(recs) == len(set(recs))

    def test_low_risk_loyal_customer_fallback(self, engine):
        customer = {
            "probability": 0.10,
            "risk_level": "Very Low",
            "Contract": "Two year",
            "tenure": 48,
            "MonthlyCharges": 40.0,
            "InternetService": "DSL",
            "TechSupport": "Yes",
        }
        recs = engine.recommend_for_row(customer)
        assert "Loyalty Program" in recs
        assert "Offer Discount" not in recs

    def test_fiber_optic_no_tech_support_trigger(self, engine):
        customer = {
            "probability": 0.30,
            "risk_level": "Low",
            "Contract": "Two year",
            "tenure": 24,
            "MonthlyCharges": 65.0,
            "InternetService": "Fiber optic",
            "TechSupport": "No",
        }
        recs = engine.recommend_for_row(customer)
        assert "Free Tech Support" in recs

    def test_generate_recommendations_dataframe(self, engine):
        data = {
            "customer_id": "TEST-01",
            "probability": 0.85,
            "Contract": "Month-to-month",
            "tenure": 2,
            "MonthlyCharges": 95.0,
        }
        df = engine.generate_recommendations(data)
        assert "Recommendations" in df.columns
        assert len(df["Recommendations"].iloc[0]) > 0


class TestRecommendationService:
    def test_service_generate(self):
        service = RecommendationService()
        data = {
            "customer_id": "TEST-02",
            "probability": 0.65,
            "Contract": "Month-to-month",
            "tenure": 8,
            "MonthlyCharges": 75.0,
        }
        results = service.generate(data)
        assert len(results) == 1
        assert "Recommendations" in results[0]
