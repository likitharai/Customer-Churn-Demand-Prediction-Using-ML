"""Prediction service — wraps the ML pipeline predict module."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "ml_pipeline"))

from src.predict import ChurnPredictor


class PredictionService:
    def __init__(self):
        self.predictor = ChurnPredictor()

    def predict(self, customer_data: dict) -> dict:
        return self.predictor.predict(customer_data)

    def get_saved_predictions(self):
        import pandas as pd
        path = Path(__file__).resolve().parents[4] / "reports" / "predictions.csv"
        if path.exists():
            return pd.read_csv(path).head(100).to_dict(orient="records")
        return []
