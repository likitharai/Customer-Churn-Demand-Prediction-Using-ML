"""Generate retention recommendations from churn and business context."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from ml_pipeline.src.config import REPORTS_DIR
from ml_pipeline.src.constants import RISK_THRESHOLDS
from ml_pipeline.src.logger import logger


class RecommendationEngine:
    """Create deterministic retention recommendations from customer features."""

    def __init__(self, reports_dir: Path | None = None) -> None:
        self.reports_dir = reports_dir or REPORTS_DIR

    @staticmethod
    def _normalize_risk_level(risk_level: str | None, probability: float | None) -> str:
        """Derive a risk label when only a probability is available."""

        if risk_level:
            return risk_level
        if probability is None:
            return "Unknown"
        if probability >= RISK_THRESHOLDS["very_high"]:
            return "Very High"
        if probability >= RISK_THRESHOLDS["high"]:
            return "High"
        if probability >= RISK_THRESHOLDS["medium"]:
            return "Medium"
        if probability >= RISK_THRESHOLDS["low"]:
            return "Low"
        return "Very Low"

    def recommend_for_row(self, row: pd.Series) -> list[str]:
        """Generate retention actions for a single customer record."""

        recommendations: list[str] = []
        risk_level = self._normalize_risk_level(
            str(row.get("Risk_Level")) if pd.notna(row.get("Risk_Level")) else None,
            float(row.get("Probability")) if pd.notna(row.get("Probability")) else None,
        )

        monthly_charges = float(row.get("MonthlyCharges", 0) or 0)
        tenure = float(row.get("tenure", 0) or 0)
        contract = str(row.get("Contract", "")).strip()
        internet_service = str(row.get("InternetService", "")).strip()
        tech_support = str(row.get("TechSupport", "")).strip()
        streaming_tv = str(row.get("StreamingTV", "")).strip()
        streaming_movies = str(row.get("StreamingMovies", "")).strip()
        paperless_billing = str(row.get("PaperlessBilling", "")).strip()
        payment_method = str(row.get("PaymentMethod", "")).strip()

        if risk_level in {"Critical", "Very High", "High"}:
            recommendations.extend(["Customer Success Call", "Offer Discount"])

        if risk_level in {"Very High", "High"} and contract == "Month-to-month":
            recommendations.append("Upgrade Contract")

        if tenure < 12:
            recommendations.append("Loyalty Program")

        if monthly_charges >= 70:
            recommendations.append("Offer Discount")

        if internet_service == "Fiber optic" and tech_support == "No":
            recommendations.append("Free Tech Support")

        if tech_support == "No" and risk_level in {"High", "Critical", "Very High"}:
            recommendations.append("Customer Success Call")

        if streaming_tv == "Yes" or streaming_movies == "Yes":
            recommendations.append("Premium Upgrade")

        if paperless_billing == "Yes" and payment_method == "Electronic check":
            recommendations.append("Customer Success Call")

        if contract in {"Month-to-month", "One year"} and tenure >= 24:
            recommendations.append("Upgrade Contract")

        if not recommendations:
            recommendations.append("Loyalty Program")

        unique_recommendations = list(dict.fromkeys(recommendations))
        logger.debug("Recommendations for customer: %s", unique_recommendations)
        return unique_recommendations

    def generate_recommendations(self, dataframe: pd.DataFrame | dict[str, Any]) -> pd.DataFrame:
        """Add recommendation text to a dataframe or single customer record."""

        if isinstance(dataframe, dict):
            dataframe = pd.DataFrame([dataframe])
        else:
            dataframe = dataframe.copy()

        dataframe["Recommendations"] = dataframe.apply( # type: ignore
            lambda row: "; ".join(self.recommend_for_row(row)),
            axis=1,
        )
        return dataframe

    def recommendation_summary(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        """Count the frequency of recommendation patterns."""

        if "Recommendations" not in dataframe.columns:
            dataframe = self.generate_recommendations(dataframe)

        exploded = dataframe["Recommendations"].str.split("; ").explode()
        summary = exploded.value_counts().rename_axis("Recommendation").reset_index(name="Count")
        return summary

    def save_recommendations(self, dataframe: pd.DataFrame, filename: str = "recommendations.csv") -> Path:
        """Persist recommendations to the reports directory."""

        self.reports_dir.mkdir(parents=True, exist_ok=True)
        output_path = self.reports_dir / filename
        dataframe.to_csv(output_path, index=False)
        logger.info("Saved recommendations to %s", output_path)
        return output_path

    def run(self, dataframe: pd.DataFrame | dict[str, Any]) -> pd.DataFrame:
        """Generate, persist, and return retention recommendations."""

        try:
            recommendations = self.generate_recommendations(dataframe)
            self.save_recommendations(recommendations)
            logger.info("Generated customer recommendations successfully")
            return recommendations
        except Exception as exc:
            logger.exception("Recommendation generation failed")
            raise RuntimeError("Recommendation engine failed") from exc


if __name__ == "__main__":
    engine = RecommendationEngine()
    sample = {
        "Risk_Level": "High",
        "Probability": 0.83,
        "MonthlyCharges": 89.0,
        "tenure": 6,
        "Contract": "Month-to-month",
        "InternetService": "Fiber optic",
        "TechSupport": "No",
        "StreamingTV": "Yes",
        "StreamingMovies": "No",
        "PaperlessBilling": "Yes",
        "PaymentMethod": "Electronic check",
    }
    print(engine.run(sample))
