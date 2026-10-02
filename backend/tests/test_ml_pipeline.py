"""Unit tests for ML Prediction Service and Model Pipeline."""

from __future__ import annotations

import pytest
from app.services.prediction_service import PredictionService


@pytest.fixture(scope="module")
def predictor():
    return PredictionService()


class TestMLPredictionService:
    def test_predictor_initialization_and_metadata(self, predictor):
        assert predictor.predictor is not None
        metadata = predictor.predictor.metadata
        assert "model_name" in metadata
        assert "model_version" in metadata
        assert metadata["model_version"] in {"1.0.0", "v1.0.0"}

    def test_single_prediction_schema(self, predictor):
        customer_data = {
            "gender": "Female",
            "SeniorCitizen": 0,
            "Partner": "Yes",
            "Dependents": "No",
            "tenure": 12,
            "PhoneService": "Yes",
            "MultipleLines": "No",
            "InternetService": "DSL",
            "OnlineSecurity": "Yes",
            "OnlineBackup": "No",
            "DeviceProtection": "No",
            "TechSupport": "Yes",
            "StreamingTV": "No",
            "StreamingMovies": "No",
            "Contract": "One year",
            "PaperlessBilling": "Yes",
            "PaymentMethod": "Mailed check",
            "MonthlyCharges": 45.0,
            "TotalCharges": 540.0,
        }
        res = predictor.predict(customer_data)
        assert "probability" in res
        assert "prediction_label" in res
        assert "risk_level" in res
        assert "prediction" in res

        assert 0.0 <= res["probability"] <= 1.0
        assert res["prediction"] in {0, 1}
        assert res["risk_level"] in {"Very Low", "Low", "Medium", "High", "Very High"}

    def test_risk_monotonicity_sanity_check(self, predictor):
        # High risk customer: brand new, month-to-month, expensive fiber, no add-ons
        high_risk_input = {
            "gender": "Male",
            "SeniorCitizen": 0,
            "Partner": "No",
            "Dependents": "No",
            "tenure": 1,
            "PhoneService": "Yes",
            "MultipleLines": "No",
            "InternetService": "Fiber optic",
            "OnlineSecurity": "No",
            "OnlineBackup": "No",
            "DeviceProtection": "No",
            "TechSupport": "No",
            "StreamingTV": "No",
            "StreamingMovies": "No",
            "Contract": "Month-to-month",
            "PaperlessBilling": "Yes",
            "PaymentMethod": "Electronic check",
            "MonthlyCharges": 85.0,
            "TotalCharges": 85.0,
        }

        # Low risk customer: 5-year loyal, two-year contract, bundled security & support
        low_risk_input = {
            "gender": "Female",
            "SeniorCitizen": 0,
            "Partner": "Yes",
            "Dependents": "Yes",
            "tenure": 60,
            "PhoneService": "Yes",
            "MultipleLines": "Yes",
            "InternetService": "DSL",
            "OnlineSecurity": "Yes",
            "OnlineBackup": "Yes",
            "DeviceProtection": "Yes",
            "TechSupport": "Yes",
            "StreamingTV": "No",
            "StreamingMovies": "No",
            "Contract": "Two year",
            "PaperlessBilling": "No",
            "PaymentMethod": "Bank transfer (automatic)",
            "MonthlyCharges": 55.0,
            "TotalCharges": 3300.0,
        }

        high_res = predictor.predict(high_risk_input)
        low_res = predictor.predict(low_risk_input)

        assert high_res["probability"] > low_res["probability"], (
            f"Expected high-risk profile probability ({high_res['probability']}) "
            f"to exceed low-risk profile ({low_res['probability']})"
        )

    def test_missing_and_imputed_features(self, predictor):
        # Input with partial/empty fields should be handled by imputer steps
        minimal_input = {
            "tenure": 10,
            "MonthlyCharges": 50.0,
            "TotalCharges": 500.0,
            "Contract": "Month-to-month",
        }
        res = predictor.predict(minimal_input)
        assert 0.0 <= res["probability"] <= 1.0
