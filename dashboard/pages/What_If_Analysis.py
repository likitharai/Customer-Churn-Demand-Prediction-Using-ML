"""What-if analysis dashboard page."""

from __future__ import annotations

import pandas as pd
import streamlit as st
from streamlit import runtime

from src.predict import ChurnPredictor
from src.recommendation_engine import RecommendationEngine


def main() -> None:
	"""Render the what-if scenario analysis page."""
	if not runtime.exists():
		return

	st.title("What-If Analysis")
	st.caption("Change customer attributes and observe churn and retention impact.")

	predictor = ChurnPredictor()
	recommendation_engine = RecommendationEngine()

	sample = {
		"gender": st.selectbox("Gender", ["Female", "Male"]),
		"SeniorCitizen": st.selectbox("Senior citizen", [0, 1]),
		"Partner": st.selectbox("Partner", ["No", "Yes"]),
		"Dependents": st.selectbox("Dependents", ["No", "Yes"]),
		"tenure": st.slider("Tenure", 0, 72, 12),
		"PhoneService": st.selectbox("Phone service", ["No", "Yes"]),
		"MultipleLines": st.selectbox("Multiple lines", ["No", "Yes", "No phone service"]),
		"InternetService": st.selectbox("Internet service", ["DSL", "Fiber optic", "No"]),
		"OnlineSecurity": st.selectbox("Online security", ["No", "Yes", "No internet service"]),
		"OnlineBackup": st.selectbox("Online backup", ["No", "Yes", "No internet service"]),
		"DeviceProtection": st.selectbox("Device protection", ["No", "Yes", "No internet service"]),
		"TechSupport": st.selectbox("Tech support", ["No", "Yes", "No internet service"]),
		"StreamingTV": st.selectbox("Streaming TV", ["No", "Yes", "No internet service"]),
		"StreamingMovies": st.selectbox("Streaming movies", ["No", "Yes", "No internet service"]),
		"Contract": st.selectbox("Contract", ["Month-to-month", "One year", "Two year"]),
		"PaperlessBilling": st.selectbox("Paperless billing", ["No", "Yes"]),
		"PaymentMethod": st.selectbox(
			"Payment method",
			[
				"Electronic check",
				"Mailed check",
				"Bank transfer (automatic)",
				"Credit card (automatic)",
			],
		),
		"MonthlyCharges": st.number_input("Monthly charges", min_value=0.0, value=70.0, step=0.1),
		"TotalCharges": st.number_input("Total charges", min_value=0.0, value=1200.0, step=1.0),
	}

	if st.button("Evaluate scenario"):
		prediction = predictor.predict(sample)
		enriched = pd.DataFrame([sample])
		enriched["Probability"] = prediction["probability"]
		enriched["Risk_Level"] = prediction["risk_level"]
		recommendation = recommendation_engine.generate_recommendations(enriched)

		st.metric("Prediction", prediction["prediction_label"], delta=f"{prediction['probability']:.1%}")
		st.dataframe(recommendation, width="stretch")


if __name__ == "__main__":
	main()
