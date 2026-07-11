"""Evaluate the trained model and persist standard performance reports."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import joblib
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.calibration import calibration_curve
from sklearn.metrics import (
    ConfusionMatrixDisplay,
    accuracy_score,
    auc,
    classification_report,
    cohen_kappa_score,
    confusion_matrix,
    f1_score,
    log_loss,
    matthews_corrcoef,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)

from ml_pipeline.src.config import MODELS_DIR, PROCESSED_DATA_DIR, REPORTS_DIR
from ml_pipeline.src.constants import ARTIFACT_FILENAMES
from ml_pipeline.src.logger import logger


class ModelEvaluator:
    """Evaluate the selected model against the holdout test split."""

    def __init__(self, models_dir: Path | None = None, reports_dir: Path | None = None) -> None:
        self.models_dir = models_dir or MODELS_DIR
        self.reports_dir = reports_dir or REPORTS_DIR
        self.model = self._load_model()
        self.reports_dir.mkdir(parents=True, exist_ok=True)

    def _load_model(self) -> Any:
        """Load the persisted best model artifact."""

        model_path = self.models_dir / ARTIFACT_FILENAMES["best_model"]
        if not model_path.exists():
            raise FileNotFoundError(f"Best model artifact not found: {model_path}")
        return joblib.load(model_path)

    def load_data(self) -> tuple[pd.DataFrame, pd.Series]:
        """Load the transformed test split from disk."""

        x_test_path = PROCESSED_DATA_DIR / "x_test.csv"
        y_test_path = PROCESSED_DATA_DIR / "y_test.csv"

        if not x_test_path.exists() or not y_test_path.exists():
            raise FileNotFoundError("Processed test data not found. Run preprocessing first.")

        X_test = pd.read_csv(x_test_path)
        y_test = pd.read_csv(y_test_path).iloc[:, 0]
        logger.info("Loaded test data: X=%s, y=%s", X_test.shape, y_test.shape)
        return X_test, y_test

    def _predict_scores(self, X_test: pd.DataFrame) -> pd.Series:
        """Return continuous scores for metric calculation."""

        if hasattr(self.model, "predict_proba"):
            scores = self.model.predict_proba(X_test)[:, 1]
        elif hasattr(self.model, "decision_function"):
            scores = self.model.decision_function(X_test)
        else:
            scores = self.model.predict(X_test)

        return pd.Series(scores, index=X_test.index)

    def predict(self) -> tuple[pd.DataFrame, pd.Series, pd.Series, pd.Series]:
        """Generate predictions and scores for the holdout split."""

        X_test, y_test = self.load_data()
        y_pred = pd.Series(self.model.predict(X_test), index=X_test.index)
        y_prob = self._predict_scores(X_test)
        return X_test, y_test, y_pred, y_prob

    def evaluate(self) -> dict[str, Any]:
        """Calculate the evaluation metrics and persist the outputs."""

        X_test, y_test, y_pred, y_prob = self.predict()

        metrics = {
            "Accuracy": accuracy_score(y_test, y_pred),
            "Precision": precision_score(y_test, y_pred, zero_division=0),
            "Recall": recall_score(y_test, y_pred, zero_division=0),
            "F1 Score": f1_score(y_test, y_pred, zero_division=0),
            "ROC AUC": roc_auc_score(y_test, y_prob),
            "Log Loss": log_loss(y_test, y_prob),
            "Matthews Correlation": matthews_corrcoef(y_test, y_pred),
            "Cohen Kappa": cohen_kappa_score(y_test, y_pred),
        }

        self.metrics = metrics
        self.classification_report = classification_report(
            y_test,
            y_pred,
            output_dict=True,
            zero_division=0,
        )
        self.confusion_matrix = confusion_matrix(y_test, y_pred)
        self.y_test = y_test
        self.y_pred = y_pred
        self.y_prob = y_prob
        self.X_test = X_test

        self._save_metrics()
        self._save_classification_report()
        self._save_confusion_matrix()
        self.plot_confusion_matrix()
        self.plot_roc_curve()
        self.plot_precision_recall_curve()
        self.plot_calibration_curve()
        logger.info("Evaluation completed successfully")
        return metrics

    def _save_metrics(self) -> Path:
        """Persist the evaluation metrics as JSON."""

        metrics_path = self.reports_dir / ARTIFACT_FILENAMES["evaluation_metrics"]
        with metrics_path.open("w", encoding="utf-8") as file:
            json.dump(self.metrics, file, indent=4)
        logger.info("Saved evaluation metrics to %s", metrics_path)
        return metrics_path

    def _save_classification_report(self) -> Path:
        """Persist the classification report as a CSV table."""

        report_path = self.reports_dir / ARTIFACT_FILENAMES["classification_report"]
        report_df = pd.DataFrame(self.classification_report).transpose()
        report_df.to_csv(report_path)
        logger.info("Saved classification report to %s", report_path)
        return report_path

    def _save_confusion_matrix(self) -> Path:
        """Persist the confusion matrix as a CSV file."""

        matrix_path = self.reports_dir / ARTIFACT_FILENAMES["confusion_matrix"]
        pd.DataFrame(self.confusion_matrix).to_csv(matrix_path, index=False)
        logger.info("Saved confusion matrix to %s", matrix_path)
        return matrix_path

    def plot_confusion_matrix(self) -> Path:
        """Plot and save the confusion matrix."""

        plot_path = self.reports_dir / "confusion_matrix.png"
        fig, ax = plt.subplots(figsize=(6, 6))
        ConfusionMatrixDisplay(confusion_matrix=self.confusion_matrix).plot(
            cmap="Blues",
            ax=ax,
            colorbar=False,
        )
        plt.title("Confusion Matrix")
        plt.tight_layout()
        plt.savefig(plot_path, dpi=300)
        plt.close(fig)
        return plot_path

    def plot_roc_curve(self) -> Path:
        """Plot and save the ROC curve."""

        plot_path = self.reports_dir / "roc_curve.png"
        fpr, tpr, _ = roc_curve(self.y_test, self.y_prob)
        roc_score = auc(fpr, tpr)

        plt.figure(figsize=(8, 6))
        plt.plot(fpr, tpr, linewidth=2, label=f"AUC = {roc_score:.4f}")
        plt.plot([0, 1], [0, 1], linestyle="--")
        plt.xlabel("False Positive Rate")
        plt.ylabel("True Positive Rate")
        plt.title("ROC Curve")
        plt.legend()
        plt.grid(True)
        plt.tight_layout()
        plt.savefig(plot_path, dpi=300)
        plt.close()
        return plot_path

    def plot_precision_recall_curve(self) -> Path:
        """Plot and save the precision-recall curve."""

        plot_path = self.reports_dir / "precision_recall_curve.png"
        precision, recall, _ = precision_recall_curve(self.y_test, self.y_prob)

        plt.figure(figsize=(8, 6))
        plt.plot(recall, precision, linewidth=2)
        plt.xlabel("Recall")
        plt.ylabel("Precision")
        plt.title("Precision Recall Curve")
        plt.grid(True)
        plt.tight_layout()
        plt.savefig(plot_path, dpi=300)
        plt.close()
        return plot_path

    def plot_calibration_curve(self) -> Path:
        """Plot and save the calibration curve."""

        plot_path = self.reports_dir / "calibration_curve.png"
        prob_true, prob_pred = calibration_curve(self.y_test, self.y_prob, n_bins=10)

        plt.figure(figsize=(8, 6))
        plt.plot(prob_pred, prob_true, marker="o")
        plt.plot([0, 1], [0, 1], linestyle="--")
        plt.xlabel("Predicted Probability")
        plt.ylabel("Observed Probability")
        plt.title("Calibration Curve")
        plt.grid(True)
        plt.tight_layout()
        plt.savefig(plot_path, dpi=300)
        plt.close()
        return plot_path

    def run(self) -> dict[str, Any]:
        """Execute the evaluation workflow."""

        try:
            return self.evaluate()
        except Exception as exc:
            logger.exception("Model evaluation failed")
            raise RuntimeError("Model evaluation pipeline failed") from exc


if __name__ == "__main__":
    evaluator = ModelEvaluator()
    evaluator.run()
