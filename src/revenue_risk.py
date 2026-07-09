"""Estimate revenue risk and executive KPIs from churn predictions."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import pandas as pd

from src.config import PROCESSED_DATA_DIR, REPORTS_DIR
from src.constants import RISK_THRESHOLDS, TARGET_COLUMN
from src.logger import logger
from src.predict import ChurnPredictor


class RevenueRiskAnalyzer:
    """Convert churn predictions into revenue-at-risk business metrics."""

    def __init__(self, data_file: Path | None = None, reports_dir: Path | None = None) -> None:
        self.data_file = data_file or (PROCESSED_DATA_DIR / "cleaned_telco.csv")
        self.reports_dir = reports_dir or REPORTS_DIR
        self.predictor = ChurnPredictor()
        self.data: pd.DataFrame | None = None
        self.summary: dict[str, Any] | None = None

    def load_dataset(self) -> pd.DataFrame:
        """Load the cleaned dataset with raw business values."""

        if not self.data_file.exists():
            raise FileNotFoundError(f"Cleaned dataset not found: {self.data_file}")

        dataframe = pd.read_csv(self.data_file)
        logger.info("Loaded revenue-risk input data with shape %s", dataframe.shape)
        return dataframe

    def predict(self) -> pd.DataFrame:
        """Generate churn probabilities for the raw customer records."""

        dataframe = self.load_dataset()
        features = dataframe.drop(columns=[TARGET_COLUMN, "Churn"], errors="ignore")
        predictions = self.predictor.predict_batch(features)

        result = dataframe.copy()
        for column in ("Prediction", "Probability", "Risk_Level"):
            if column in predictions.columns:
                result[column] = predictions[column].values

        if TARGET_COLUMN in result.columns:
            result["Actual_Churn"] = result[TARGET_COLUMN]

        self.data = result
        logger.info("Generated churn predictions for revenue-risk analysis")
        return result

    @staticmethod
    def estimate_clv(monthly_charge: float, tenure: float) -> float:
        """Estimate customer lifetime value from monthly charge and tenure."""

        return float(monthly_charge) * float(tenure)

    def calculate_revenue_risk(self) -> pd.DataFrame:
        """Calculate customer-level CLV and revenue at risk."""

        dataframe = self.predict()
        required_columns = {"MonthlyCharges", "tenure", "Probability"}
        missing_columns = required_columns.difference(dataframe.columns)
        if missing_columns:
            raise KeyError(f"Missing required revenue-risk columns: {sorted(missing_columns)}")

        dataframe = dataframe.copy()
        dataframe["Estimated_CLV"] = dataframe.apply(
            lambda row: self.estimate_clv(row["MonthlyCharges"], row["tenure"]),
            axis=1,
        )
        dataframe["Revenue_Risk"] = dataframe["Estimated_CLV"] * dataframe["Probability"]
        dataframe["Retention_Cost"] = dataframe["Revenue_Risk"] * 0.25
        dataframe["Expected_Revenue_Saved"] = dataframe["Revenue_Risk"] - dataframe["Retention_Cost"]
        self.data = dataframe
        logger.info("Calculated revenue-risk columns")
        return dataframe

    def customer_segmentation(self) -> pd.DataFrame:
        """Assign business risk segments from churn probability."""

        if self.data is None:
            self.calculate_revenue_risk()

        dataframe = self.data.copy()
        dataframe["Risk_Level"] = "Very Low"
        dataframe.loc[dataframe["Probability"] >= RISK_THRESHOLDS["low"], "Risk_Level"] = "Low"
        dataframe.loc[dataframe["Probability"] >= RISK_THRESHOLDS["medium"], "Risk_Level"] = "Medium"
        dataframe.loc[dataframe["Probability"] >= RISK_THRESHOLDS["high"], "Risk_Level"] = "High"
        dataframe.loc[dataframe["Probability"] >= RISK_THRESHOLDS["very_high"], "Risk_Level"] = "Critical"
        self.data = dataframe
        logger.info("Assigned customer risk segments")
        return dataframe

    def high_risk_customers(self, threshold: float = RISK_THRESHOLDS["very_high"]) -> pd.DataFrame:
        """Return the customers most likely to churn."""

        if self.data is None:
            self.customer_segmentation()

        dataframe = self.data.copy()
        high_risk = dataframe[dataframe["Probability"] >= threshold].sort_values(
            by="Revenue_Risk",
            ascending=False,
        )
        high_risk.to_csv(self.reports_dir / "high_risk_customers.csv", index=False)
        logger.info("Saved %s high-risk customers", len(high_risk))
        return high_risk

    def revenue_summary(self) -> dict[str, Any]:
        """Generate a summary of revenue-at-risk metrics."""

        if self.data is None:
            self.customer_segmentation()

        dataframe = self.data.copy()
        summary = {
            "Total_Customers": int(len(dataframe)),
            "Predicted_Churn": int(dataframe["Prediction"].sum()),
            "Total_Revenue_Risk": round(float(dataframe["Revenue_Risk"].sum()), 2),
            "Average_CLV": round(float(dataframe["Estimated_CLV"].mean()), 2),
            "Average_Churn_Probability": round(float(dataframe["Probability"].mean()), 4),
            "Monthly_Revenue_Loss": round(
                float((dataframe["MonthlyCharges"] * dataframe["Probability"]).sum()),
                2,
            ),
            "Retention_Cost": round(float(dataframe["Retention_Cost"].sum()), 2),
            "Expected_Revenue_Saved": round(float(dataframe["Expected_Revenue_Saved"].sum()), 2),
        }
        self.summary = summary
        pd.DataFrame([summary]).to_csv(self.reports_dir / "revenue_risk_summary.csv", index=False)
        logger.info("Saved revenue summary")
        return summary

    def revenue_by_segment(self) -> pd.DataFrame:
        """Aggregate revenue risk by customer risk segment."""

        if self.data is None:
            self.customer_segmentation()

        dataframe = self.data.copy()
        report = (
            dataframe.groupby("Risk_Level")
            .agg(
                Customers=("Risk_Level", "count"),
                Revenue_Risk=("Revenue_Risk", "sum"),
                Avg_CLV=("Estimated_CLV", "mean"),
                Avg_Probability=("Probability", "mean"),
            )
            .reset_index()
            .sort_values(by="Revenue_Risk", ascending=False)
        )
        report.to_csv(self.reports_dir / "revenue_risk_by_segment.csv", index=False)
        logger.info("Saved revenue-by-segment report")
        return report

    def executive_kpis(self) -> dict[str, Any]:
        """Build the executive KPI snapshot used by the dashboard."""

        if self.data is None:
            self.customer_segmentation()

        dataframe = self.data.copy()
        kpis = {
            "Total Customers": int(len(dataframe)),
            "Active Customers": int((dataframe["Prediction"] == 0).sum()),
            "Churn Customers": int((dataframe["Prediction"] == 1).sum()),
            "Revenue": round(float(dataframe["MonthlyCharges"].sum()), 2),
            "Revenue At Risk": round(float(dataframe["Revenue_Risk"].sum()), 2),
            "Customer Lifetime Value": round(float(dataframe["Estimated_CLV"].mean()), 2),
            "Retention Savings": round(float(dataframe["Expected_Revenue_Saved"].sum()), 2),
        }
        output_path = self.reports_dir / "executive_kpis.json"
        with output_path.open("w", encoding="utf-8") as file:
            json.dump(kpis, file, indent=4)
        logger.info("Saved executive KPIs")
        return kpis

    def plot_revenue_risk(self) -> Path:
        """Plot revenue risk by customer segment."""

        if self.data is None:
            self.customer_segmentation()

        dataframe = self.data.copy()
        plot_data = dataframe.groupby("Risk_Level")["Revenue_Risk"].sum().sort_values(ascending=False)
        plot_path = self.reports_dir / "revenue_risk_by_segment.png"

        plt.figure(figsize=(8, 5))
        plot_data.plot(kind="bar", color="#0f766e")
        plt.title("Revenue Risk by Segment")
        plt.xlabel("Risk Level")
        plt.ylabel("Revenue at Risk")
        plt.tight_layout()
        plt.savefig(plot_path, dpi=300)
        plt.close()
        logger.info("Saved revenue risk plot to %s", plot_path)
        return plot_path

    def run(self) -> dict[str, Any]:
        """Execute the full revenue-risk workflow."""

        try:
            self.calculate_revenue_risk()
            self.customer_segmentation()
            high_risk = self.high_risk_customers()
            summary = self.revenue_summary()
            segment_report = self.revenue_by_segment()
            kpis = self.executive_kpis()
            self.plot_revenue_risk()

            if self.data is not None:
                self.data.to_csv(self.reports_dir / "revenue_risk_analysis.csv", index=False)

            logger.info("Revenue-risk analysis completed successfully")
            return {
                "summary": summary,
                "segment_report": segment_report,
                "high_risk_customers": high_risk,
                "executive_kpis": kpis,
            }
        except Exception as exc:
            logger.exception("Revenue-risk analysis failed")
            raise RuntimeError("Revenue-risk pipeline failed") from exc


if __name__ == "__main__":
    analyzer = RevenueRiskAnalyzer()
    analyzer.run()
