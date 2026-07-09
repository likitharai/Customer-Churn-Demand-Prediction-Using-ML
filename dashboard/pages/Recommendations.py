"""Recommendations dashboard page."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st
from streamlit import runtime

from src.recommendation_engine import RecommendationEngine


PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPORTS_DIR = PROJECT_ROOT / "reports"


def main() -> None:
	"""Render the retention recommendation page."""

	if not runtime.exists():
		return

	st.title("Recommendations")
	st.caption("Rules-based retention actions for churn-risk customers.")

	engine = RecommendationEngine()

	sample_input = {
		"Risk_Level": st.selectbox("Risk level", ["Very Low", "Low", "Medium", "High", "Very High", "Critical"]),
		"Probability": st.slider("Churn probability", 0.0, 1.0, 0.75, 0.01),
		"MonthlyCharges": st.number_input("Monthly charges", min_value=0.0, value=75.0, step=1.0),
		"tenure": st.number_input("Tenure", min_value=0.0, value=12.0, step=1.0),
		"Contract": st.selectbox("Contract", ["Month-to-month", "One year", "Two year"]),
		"InternetService": st.selectbox("Internet service", ["DSL", "Fiber optic", "No"]),
		"TechSupport": st.selectbox("Tech support", ["Yes", "No", "No internet service"]),
		"StreamingTV": st.selectbox("Streaming TV", ["Yes", "No", "No internet service"]),
		"StreamingMovies": st.selectbox("Streaming movies", ["Yes", "No", "No internet service"]),
		"PaperlessBilling": st.selectbox("Paperless billing", ["Yes", "No"]),
		"PaymentMethod": st.selectbox(
			"Payment method",
			[
				"Electronic check",
				"Mailed check",
				"Bank transfer (automatic)",
				"Credit card (automatic)",
			],
		),
	}

	if st.button("Generate recommendation"):
		recommendation_df = engine.run(sample_input)
		st.dataframe(recommendation_df, width="stretch")

	recommendations_path = REPORTS_DIR / "recommendations.csv"
	if recommendations_path.exists():
		st.subheader("Saved Recommendations")
		st.dataframe(pd.read_csv(recommendations_path).head(25), width="stretch")


if __name__ == "__main__":
	main()
