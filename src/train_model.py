"""Train and compare churn models, then persist the best performer."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.tree import DecisionTreeClassifier

from src.config import MODELS_DIR, PROCESSED_DATA_DIR
from src.constants import ARTIFACT_FILENAMES, CV_FOLDS, MODEL_COMPARE_ORDER, RANDOM_STATE
from src.logger import logger
from src.model_config import ModelFactory


class ModelTrainer:
    """Compare candidate models and persist the best one for production use."""

    def __init__(self, data_dir: Path | None = None, models_dir: Path | None = None) -> None:
        self.data_dir = data_dir or PROCESSED_DATA_DIR
        self.models_dir = models_dir or MODELS_DIR
        self.models = self._build_models()
        self.best_model: BaseEstimator | None = None
        self.best_model_name: str | None = None
        self.best_roc_auc: float = float("-inf")
        self.best_accuracy: float = float("-inf")
        self.results: list[dict[str, Any]] = []

    def _build_models(self) -> dict[str, BaseEstimator]:
        """Build the default comparison models in the requested order."""

        available_models = ModelFactory.available_models()
        models: dict[str, BaseEstimator] = {}

        for model_name in MODEL_COMPARE_ORDER:
            model = available_models.get(model_name)
            if model is None:
                logger.warning("Skipping unavailable model: %s", model_name)
                continue
            models[model_name] = model

        return models

    def load_data(self) -> tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
        """Load the processed train/test splits from disk."""

        x_train_path = self.data_dir / "x_train.csv"
        x_test_path = self.data_dir / "x_test.csv"
        y_train_path = self.data_dir / "y_train.csv"
        y_test_path = self.data_dir / "y_test.csv"

        for path in (x_train_path, x_test_path, y_train_path, y_test_path):
            if not path.exists():
                raise FileNotFoundError(f"Required processed dataset not found: {path}")

        X_train = pd.read_csv(x_train_path)
        X_test = pd.read_csv(x_test_path)
        y_train = pd.read_csv(y_train_path).iloc[:, 0]
        y_test = pd.read_csv(y_test_path).iloc[:, 0]

        logger.info("Loaded training data: train=%s, test=%s", X_train.shape, X_test.shape)
        return X_train, X_test, y_train, y_test

    @staticmethod
    def _get_score_vector(model: BaseEstimator, X: pd.DataFrame) -> np.ndarray:
        """Return a continuous score vector for ROC AUC calculations."""

        if hasattr(model, "predict_proba"):
            return model.predict_proba(X)[:, 1]
        if hasattr(model, "decision_function"):
            return model.decision_function(X)
        return model.predict(X)

    def cross_validation(self, model: BaseEstimator, X: pd.DataFrame, y: pd.Series) -> float:
        """Measure ROC AUC with stratified cross-validation."""

        cv = StratifiedKFold(n_splits=CV_FOLDS, shuffle=True, random_state=RANDOM_STATE)
        scores = cross_val_score(model, X, y, cv=cv, scoring="roc_auc")
        return float(scores.mean())

    def evaluate(self, model: BaseEstimator, X_test: pd.DataFrame, y_test: pd.Series) -> dict[str, Any]:
        """Evaluate a trained model on the holdout test split."""

        predictions = model.predict(X_test)
        scores = self._get_score_vector(model, X_test)

        metrics = {
            "Accuracy": accuracy_score(y_test, predictions),
            "Precision": precision_score(y_test, predictions, zero_division=0),
            "Recall": recall_score(y_test, predictions, zero_division=0),
            "F1 Score": f1_score(y_test, predictions, zero_division=0),
            "ROC_AUC": roc_auc_score(y_test, scores),
            "Confusion_Matrix": confusion_matrix(y_test, predictions),
            "Classification_Report": classification_report(
                y_test,
                predictions,
                output_dict=True,
                zero_division=0,
            ),
        }
        return metrics

    def _fit_model(self, model: BaseEstimator, X_train: pd.DataFrame, y_train: pd.Series) -> BaseEstimator:
        """Fit a model and return the fitted instance."""

        fitted_model = model.fit(X_train, y_train)
        return fitted_model

    def train_models(self) -> tuple[BaseEstimator, pd.DataFrame, pd.DataFrame]:
        """Train all supported models and select the best one by ROC AUC."""

        X_train, X_test, y_train, y_test = self.load_data()

        logger.info("Starting model comparison")
        self.results = []
        self.best_model = None
        self.best_model_name = None
        self.best_roc_auc = float("-inf")
        self.best_accuracy = float("-inf")

        for model_name, model in self.models.items():
            logger.info("Training model: %s", model_name)
            fitted_model = self._fit_model(model, X_train, y_train)
            metrics = self.evaluate(fitted_model, X_test, y_test)
            cv_score = self.cross_validation(fitted_model, X_train, y_train)

            result = {
                "Model": model_name,
                "Accuracy": round(float(metrics["Accuracy"]), 4),
                "Precision": round(float(metrics["Precision"]), 4),
                "Recall": round(float(metrics["Recall"]), 4),
                "F1 Score": round(float(metrics["F1 Score"]), 4),
                "ROC_AUC": round(float(metrics["ROC_AUC"]), 4),
                "Cross_Validation": round(cv_score, 4),
            }
            self.results.append(result)

            if metrics["ROC_AUC"] > self.best_roc_auc:
                self.best_roc_auc = float(metrics["ROC_AUC"])
                self.best_accuracy = float(metrics["Accuracy"])
                self.best_model = fitted_model
                self.best_model_name = model_name

            logger.info(
                "Model %s -> Accuracy=%.4f Precision=%.4f Recall=%.4f F1=%.4f ROC_AUC=%.4f CV=%.4f",
                model_name,
                metrics["Accuracy"],
                metrics["Precision"],
                metrics["Recall"],
                metrics["F1 Score"],
                metrics["ROC_AUC"],
                cv_score,
            )

        if self.best_model is None or self.best_model_name is None:
            raise RuntimeError("No model could be trained successfully")

        results_df = pd.DataFrame(self.results).sort_values(by="ROC_AUC", ascending=False)
        logger.info("Best model selected: %s", self.best_model_name)
        return self.best_model, results_df, X_train

    def save_best_model(self) -> Path:
        """Persist the best model as the production artifact."""

        if self.best_model is None:
            raise RuntimeError("Best model is not available")

        self.models_dir.mkdir(parents=True, exist_ok=True)
        model_path = self.models_dir / ARTIFACT_FILENAMES["best_model"]
        joblib.dump(self.best_model, model_path)
        logger.info("Saved best model to %s", model_path)
        return model_path

    def save_metrics(self) -> Path:
        """Persist the model comparison table."""

        metrics_path = self.models_dir / ARTIFACT_FILENAMES["model_metrics"]
        results_df = pd.DataFrame(self.results).sort_values(by="ROC_AUC", ascending=False)
        results_df.to_csv(metrics_path, index=False)
        logger.info("Saved model metrics to %s", metrics_path)
        return metrics_path

    def save_best_model_info(self) -> Path:
        """Persist metadata about the selected best model."""

        if self.best_model_name is None:
            raise RuntimeError("Best model name is not available")

        info = {
            "best_model": self.best_model_name,
            "accuracy": round(self.best_accuracy, 4),
            "roc_auc": round(self.best_roc_auc, 4),
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        }

        info_path = self.models_dir / ARTIFACT_FILENAMES["best_model_info"]
        with info_path.open("w", encoding="utf-8") as file:
            json.dump(info, file, indent=4)

        logger.info("Saved best model info to %s", info_path)
        return info_path

    def save_feature_importance(self, X_train: pd.DataFrame) -> Path | None:
        """Persist feature importance or coefficients for the best model."""

        if self.best_model is None:
            raise RuntimeError("Best model is not available")

        importance_path = self.models_dir / ARTIFACT_FILENAMES["feature_importance"]

        if hasattr(self.best_model, "feature_importances_"):
            importance = pd.DataFrame(
                {
                    "Feature": X_train.columns,
                    "Importance": self.best_model.feature_importances_,
                }
            ).sort_values(by="Importance", ascending=False)
            importance.to_csv(importance_path, index=False)
            logger.info("Saved tree-based feature importance to %s", importance_path)
            return importance_path

        if hasattr(self.best_model, "coef_"):
            coefficients = np.abs(np.ravel(self.best_model.coef_))
            importance = pd.DataFrame(
                {
                    "Feature": X_train.columns[: len(coefficients)],
                    "Importance": coefficients,
                }
            ).sort_values(by="Importance", ascending=False)
            importance.to_csv(importance_path, index=False)
            logger.info("Saved coefficient-based feature importance to %s", importance_path)
            return importance_path

        logger.info("Best model does not expose feature importance")
        return None

    def run(self) -> dict[str, Any]:
        """Execute the full model comparison and persistence workflow."""

        try:
            best_model, results_df, X_train = self.train_models()
            self.save_best_model()
            self.save_metrics()
            self.save_best_model_info()
            self.save_feature_importance(X_train)

            logger.info("Model training completed successfully")
            return {
                "best_model": best_model,
                "model_metrics": results_df,
                "best_model_name": self.best_model_name,
            }
        except Exception as exc:
            logger.exception("Model training failed")
            raise RuntimeError("Model training pipeline failed") from exc


if __name__ == "__main__":
    trainer = ModelTrainer()
    trainer.run()
