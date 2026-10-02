"""Prediction service — loads the authoritative model pipeline and performs inference."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import joblib
import pandas as pd

from app.services.business_rules import (
    DEFAULT_CHURN_THRESHOLD,
    is_churn_likely,
    risk_level,
)

ROOT_DIR = Path(__file__).resolve().parents[3]
DEFAULT_MODEL_PATH = ROOT_DIR / "model_pipeline.pkl"

NUMERIC_FEATURES = ["tenure", "MonthlyCharges", "TotalCharges"]
CATEGORICAL_FEATURES = [
    "gender",
    "SeniorCitizen",
    "Partner",
    "Dependents",
    "PhoneService",
    "MultipleLines",
    "InternetService",
    "OnlineSecurity",
    "OnlineBackup",
    "DeviceProtection",
    "TechSupport",
    "StreamingTV",
    "StreamingMovies",
    "Contract",
    "PaperlessBilling",
    "PaymentMethod",
]
ALL_FEATURES = NUMERIC_FEATURES + CATEGORICAL_FEATURES


class ChurnPredictor:
    """Inference engine wrapping the persisted scikit-learn Pipeline."""

    def __init__(self, model_path: Path | str | None = None, threshold: float = DEFAULT_CHURN_THRESHOLD) -> None:
        self.model_path = Path(model_path or os.getenv("MODEL_PATH", str(DEFAULT_MODEL_PATH)))
        self.threshold = float(os.getenv("CHURN_DECISION_THRESHOLD", str(threshold)))
        self.model = self._load_model()
        self.metadata = {
            "model_name": "LightGBM",
            "model_version": os.getenv("MODEL_VERSION", "v1.0.0"),
            "artifact_path": str(self.model_path),
            "features_count": len(ALL_FEATURES),
            "decision_threshold": self.threshold,
        }

    def _load_model(self) -> Any:
        if not self.model_path.exists():
            raise FileNotFoundError(f"Authoritative model artifact not found at: {self.model_path}")
        return joblib.load(self.model_path)

    def _format_input(self, customer_data: Any) -> pd.DataFrame:
        """Format input into a DataFrame matching expected feature names and types."""
        if hasattr(customer_data, "dict"):
            data = customer_data.dict()
        elif isinstance(customer_data, dict):
            data = dict(customer_data)
        elif isinstance(customer_data, pd.DataFrame):
            data = customer_data.to_dict(orient="records")[0]
        else:
            raise TypeError("Customer data must be a dict, Pydantic model, or DataFrame")

        # Normalize key names if casing differences exist
        normalized = {}
        for key, val in data.items():
            normalized[key] = val

        # Handle numeric types
        for num_col in NUMERIC_FEATURES:
            val = normalized.get(num_col, 0.0)
            try:
                normalized[num_col] = float(val) if val is not None else 0.0
            except (ValueError, TypeError):
                normalized[num_col] = 0.0

        # Handle categorical types
        for cat_col in CATEGORICAL_FEATURES:
            val = normalized.get(cat_col, "Missing")
            normalized[cat_col] = str(val) if val is not None else "Missing"

        # Build DataFrame with strictly ordered features
        df = pd.DataFrame([normalized])
        for col in ALL_FEATURES:
            if col not in df.columns:
                df[col] = 0.0 if col in NUMERIC_FEATURES else "Missing"

        return df[ALL_FEATURES]

    def predict(self, customer_data: Any) -> dict[str, Any]:
        """Generate prediction, probability, and risk level for a single customer."""
        df = self._format_input(customer_data)

        # Get probability
        if hasattr(self.model, "predict_proba"):
            prob = float(self.model.predict_proba(df)[0, 1])
        elif hasattr(self.model, "decision_function"):
            score = float(self.model.decision_function(df)[0])
            prob = float(1.0 / (1.0 + pd.np.exp(-score)))
        else:
            pred = int(self.model.predict(df)[0])
            prob = float(pred)

        pred_class = 1 if is_churn_likely(prob, self.threshold) else 0
        risk = risk_level(prob)

        return {
            "prediction": pred_class,
            "prediction_label": "Churn likely" if pred_class == 1 else "Churn unlikely",
            "probability": round(prob, 4),
            "risk_level": risk,
            "decision_threshold": self.threshold,
        }

    def predict_batch(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        """Score a batch DataFrame and return copy with Prediction, Probability, Risk_Level."""
        results = []
        for _, row in dataframe.iterrows():
            res = self.predict(row.to_dict())
            results.append(res)
        res_df = pd.DataFrame(results)
        output = dataframe.copy()
        output["Prediction"] = res_df["prediction"].values
        output["Probability"] = res_df["probability"].values
        output["Risk_Level"] = res_df["risk_level"].values
        output["Prediction_Label"] = res_df["prediction_label"].values
        return output

    def save_predictions(self, results: pd.DataFrame, output_path: Path | str | None = None) -> Path:
        target = Path(output_path) if output_path else (ROOT_DIR / "reports" / "predictions.csv")
        target.parent.mkdir(parents=True, exist_ok=True)
        results.to_csv(target, index=False)
        return target


class PredictionService:
    def __init__(self, model_path: Path | str | None = None):
        self.predictor = ChurnPredictor(model_path=model_path)

    def predict(self, customer_data: dict | Any) -> dict[str, Any]:
        return self.predictor.predict(customer_data)

    def get_saved_predictions(self):
        reports_path = ROOT_DIR / "reports" / "predictions.csv"
        if reports_path.exists():
            return pd.read_csv(reports_path).head(100).to_dict(orient="records")
        return []
