"""Recommendation service — deterministic business rules for customer retention."""

from __future__ import annotations

from typing import Any
import pandas as pd

from app.services.business_rules import risk_level as get_risk_level


class RecommendationEngine:
    """Deterministic business-rule retention playbook engine."""

    def recommend_for_row(self, row: dict[str, Any] | pd.Series) -> list[str]:
        recommendations: list[str] = []
        prob = float(row.get("Probability", row.get("probability", 0.0)) or 0.0)
        risk = str(row.get("Risk_Level", row.get("risk_level", "")) or get_risk_level(prob))

        monthly_charges = float(row.get("MonthlyCharges", row.get("monthly_charges", 0.0)) or 0.0)
        tenure = float(row.get("tenure", 0.0) or 0.0)
        contract = str(row.get("Contract", row.get("contract", ""))).strip()
        internet_service = str(row.get("InternetService", row.get("internet_service", ""))).strip()
        tech_support = str(row.get("TechSupport", row.get("tech_support", ""))).strip()
        streaming_tv = str(row.get("StreamingTV", row.get("streaming_tv", ""))).strip()
        streaming_movies = str(row.get("StreamingMovies", row.get("streaming_movies", ""))).strip()
        paperless_billing = str(row.get("PaperlessBilling", row.get("paperless_billing", ""))).strip()
        payment_method = str(row.get("PaymentMethod", row.get("payment_method", ""))).strip()

        if risk in {"Critical", "Very High", "High"}:
            recommendations.extend(["Customer Success Call", "Offer Discount"])

        if risk in {"Very High", "High"} and contract == "Month-to-month":
            recommendations.append("Upgrade Contract")

        if tenure < 12:
            recommendations.append("Loyalty Program")

        if monthly_charges >= 70:
            recommendations.append("Offer Discount")

        if internet_service == "Fiber optic" and tech_support == "No":
            recommendations.append("Free Tech Support")

        if tech_support == "No" and risk in {"High", "Critical", "Very High"}:
            recommendations.append("Customer Success Call")

        if streaming_tv == "Yes" or streaming_movies == "Yes":
            recommendations.append("Premium Upgrade")

        if paperless_billing == "Yes" and payment_method == "Electronic check":
            recommendations.append("Customer Success Call")

        if contract in {"Month-to-month", "One year"} and tenure >= 24:
            recommendations.append("Upgrade Contract")

        if not recommendations:
            recommendations.append("Loyalty Program")

        # Deduplicate while preserving order
        return list(dict.fromkeys(recommendations))

    def generate_recommendations(self, dataframe: pd.DataFrame | dict[str, Any]) -> pd.DataFrame:
        if isinstance(dataframe, dict):
            df = pd.DataFrame([dataframe])
        else:
            df = dataframe.copy()

        df["Recommendations"] = df.apply(
            lambda r: "; ".join(self.recommend_for_row(r.to_dict())),
            axis=1,
        )
        return df


class RecommendationService:
    def __init__(self):
        self.engine = RecommendationEngine()

    def generate(self, customer_data: dict) -> list[dict[str, Any]]:
        df = pd.DataFrame([customer_data])
        result = self.engine.generate_recommendations(df)
        return result.to_dict(orient="records")
