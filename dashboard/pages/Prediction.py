"""Prediction dashboard page."""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure project root is on sys.path so `src.*` imports resolve correctly
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pandas as pd
import streamlit as st
from streamlit import runtime

from src.predict import ChurnPredictor


PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPORTS_DIR = PROJECT_ROOT / "reports"


def main() -> None:
    """Render the prediction page."""

    if not runtime.exists():
        return

    st.title("Prediction")
    st.caption("Run single or batch churn prediction with the persisted model.")

    predictor = ChurnPredictor()

    uploaded_file = st.file_uploader("Upload a CSV for batch prediction", type=["csv"])
    if uploaded_file is not None and st.button("Predict uploaded CSV"):
        dataframe = pd.read_csv(uploaded_file)
        results = predictor.predict_batch(dataframe)
        st.dataframe(results.head(50), use_container_width=True)
        predictor.save_predictions(results)

    st.subheader("Saved predictions")
    saved_predictions = REPORTS_DIR / "predictions.csv"
    if saved_predictions.exists():
        st.dataframe(pd.read_csv(saved_predictions).head(25), use_container_width=True)


if __name__ == "__main__":
    main()
