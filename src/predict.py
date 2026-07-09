"""Run churn predictions using the persisted model and preprocessing pipeline."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import joblib
import pandas as pd

from src.config import MODELS_DIR, PROCESSED_DATA_DIR, REPORTS_DIR
from src.constants import ARTIFACT_FILENAMES, RISK_THRESHOLDS
from src.logger import logger


class ChurnPredictor:
    """Load the trained model and pipeline to score new customer data."""

    def __init__(self, models_dir: Path | None = None) -> None:
        self.models_dir = models_dir or MODELS_DIR
        self.model = self._load_artifact(ARTIFACT_FILENAMES["best_model"])
        self.pipeline = self._load_artifact(ARTIFACT_FILENAMES["preprocessing_pipeline"])
        self.feature_columns = self._load_optional_feature_columns()

    def _load_artifact(self, filename: str) -> Any:
        """Load a persisted artifact from the models directory."""

        path = self.models_dir / filename
        if not path.exists():
            raise FileNotFoundError(f"Required artifact not found: {path}")
        return joblib.load(path)

    def _load_optional_feature_columns(self) -> list[str] | None:
        """Load persisted feature columns when available."""

        path = self.models_dir / ARTIFACT_FILENAMES["feature_columns"]
        if not path.exists():
            return None
        feature_columns = joblib.load(path)
        return [str(column) for column in feature_columns]

    @staticmethod
    def risk_level(probability: float) -> str:
        """Convert a churn probability into a business risk label."""

        if probability >= RISK_THRESHOLDS["very_high"]:
            return "Very High"
        if probability >= RISK_THRESHOLDS["high"]:
            return "High"
        if probability >= RISK_THRESHOLDS["medium"]:
            return "Medium"
        if probability >= RISK_THRESHOLDS["low"]:
            return "Low"
        return "Very Low"

    @staticmethod
    def _ensure_dataframe(customer_data: Any) -> pd.DataFrame:
        """Normalize input data into a dataframe."""

        if isinstance(customer_data, pd.DataFrame):
            return customer_data.copy()
        if isinstance(customer_data, dict):
            return pd.DataFrame([customer_data])
        raise TypeError("Customer data must be a dictionary or pandas DataFrame")

    def _prepare_raw_input(self, customer_data: Any) -> pd.DataFrame:
        """Prepare raw customer data before it enters the pipeline."""

        dataframe = self._ensure_dataframe(customer_data)
        dataframe = dataframe.drop(columns=["Churn", "Churn_flag", "Unnamed: 0"], errors="ignore")
        dataframe = dataframe.drop(columns=["customerID"], errors="ignore")
        return dataframe

    def transform_input(self, customer_data: Any) -> pd.DataFrame:
        """Transform raw input data into the model feature space."""

        raw_dataframe = self._prepare_raw_input(customer_data)
        transformed = self.pipeline.transform(raw_dataframe)

        feature_names = self.feature_columns or list(self.pipeline.get_feature_names_out())
        transformed_dataframe = pd.DataFrame(transformed, columns=feature_names, index=raw_dataframe.index)
        return transformed_dataframe

    def predict(self, customer_data: Any) -> dict[str, Any]:
        """Predict churn for a single customer record."""

        transformed = self.transform_input(customer_data)
        prediction = int(self.model.predict(transformed)[0])
        probability = float(self._predict_probability(transformed)[0])
        risk = self.risk_level(probability)

        result = {
            "prediction": prediction,
            "probability": round(probability, 4),
            "risk_level": risk,
            "prediction_label": "Churn likely" if prediction == 1 else "Churn unlikely",
        }
        logger.info("Single prediction generated: %s", result)
        return result

    def _predict_probability(self, transformed_data: pd.DataFrame) -> pd.Series:
        """Return churn probabilities for transformed customer records."""

        if hasattr(self.model, "predict_proba"):
            return pd.Series(self.model.predict_proba(transformed_data)[:, 1], index=transformed_data.index)
        if hasattr(self.model, "decision_function"):
            scores = self.model.decision_function(transformed_data)
            return pd.Series(scores, index=transformed_data.index)
        return pd.Series(self.model.predict(transformed_data), index=transformed_data.index)

    def predict_batch(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        """Predict churn for a batch of customers."""

        transformed = self.transform_input(dataframe)
        predictions = self.model.predict(transformed)
        probabilities = self._predict_probability(transformed)

        result = self._ensure_dataframe(dataframe).copy()
        result["Prediction"] = predictions.astype(int)
        result["Probability"] = probabilities.round(4)
        result["Risk_Level"] = result["Probability"].apply(self.risk_level)

        if self.feature_columns is not None and len(self.feature_columns) != transformed.shape[1]:
            logger.warning(
                "Feature column count mismatch: saved=%s transformed=%s",
                len(self.feature_columns),
                transformed.shape[1],
            )

        logger.info("Batch prediction completed for %s records", len(result))
        return result

    def prediction_summary(self, dataframe: pd.DataFrame) -> dict[str, Any]:
        """Create a compact summary of the prediction output."""

        summary = {
            "total_customers": int(len(dataframe)),
            "predicted_churn": int((dataframe["Prediction"] == 1).sum()),
            "predicted_retained": int((dataframe["Prediction"] == 0).sum()),
            "high_risk_customers": int((dataframe["Risk_Level"] == "Very High").sum()),
            "average_probability": round(float(dataframe["Probability"].mean()), 4),
        }
        logger.info("Prediction summary: %s", summary)
        return summary

    def save_predictions(self, dataframe: pd.DataFrame, filename: str | None = None) -> Path:
        """Persist prediction results for downstream reporting."""

        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        output_path = REPORTS_DIR / (filename or ARTIFACT_FILENAMES["predictions"])
        dataframe.to_csv(output_path, index=False)
        logger.info("Saved predictions to %s", output_path)
        return output_path

    @staticmethod
    def high_risk_customers(dataframe: pd.DataFrame, threshold: float = RISK_THRESHOLDS["very_high"]) -> pd.DataFrame:
        """Return the subset of customers with the highest churn risk."""

        if "Probability" not in dataframe.columns:
            raise KeyError("Prediction dataframe must contain a Probability column")
        return dataframe[dataframe["Probability"] >= threshold].sort_values(by="Probability", ascending=False)

    def predict_csv(self, csv_path: str | Path) -> pd.DataFrame:
        """Load a CSV file and generate batch predictions."""

        csv_file = Path(csv_path)
        if not csv_file.exists():
            raise FileNotFoundError(f"Prediction input file not found: {csv_file}")

        dataframe = pd.read_csv(csv_file)
        predictions = self.predict_batch(dataframe)
        self.save_predictions(predictions)
        self.prediction_summary(predictions)
        logger.info("Generated predictions for CSV input: %s", csv_file)
        return predictions


if __name__ == "__main__":
    predictor = ChurnPredictor()
    sample = {
        "gender": "Female",
        "SeniorCitizen": 0,
        "Partner": "Yes",
        "Dependents": "No",
        "tenure": 10,
        "PhoneService": "Yes",
        "MultipleLines": "No",
        "InternetService": "Fiber optic",
        "OnlineSecurity": "No",
        "OnlineBackup": "Yes",
        "DeviceProtection": "No",
        "TechSupport": "No",
        "StreamingTV": "Yes",
        "StreamingMovies": "No",
        "Contract": "Month-to-month",
        "PaperlessBilling": "Yes",
        "PaymentMethod": "Electronic check",
        "MonthlyCharges": 80.0,
        "TotalCharges": 800.0,
    }
    print(predictor.predict(sample))
