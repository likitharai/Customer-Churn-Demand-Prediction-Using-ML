"""Model performance dashboard page."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st
from streamlit import runtime


PROJECT_ROOT = Path(__file__).resolve().parents[2]
MODELS_DIR = PROJECT_ROOT / "models"
REPORTS_DIR = PROJECT_ROOT / "reports"


def load_csv(path: Path) -> pd.DataFrame | None:
	"""Load a CSV file when available."""

	if not path.exists():
		return None
	return pd.read_csv(path)


def load_json(path: Path) -> dict[str, object]:
	"""Load a JSON file when available."""

	if not path.exists():
		return {}
	with path.open("r", encoding="utf-8") as file:
		return json.load(file)


def main() -> None:
	"""Render the model performance page."""

	if not runtime.exists():
		return

	st.title("Model Performance")
	st.caption("Compare trained models and inspect evaluation outputs.")

	metrics_df = load_csv(MODELS_DIR / "model_metrics.csv")
	best_model_info = load_json(MODELS_DIR / "best_model_info.json")
	evaluation_metrics = load_json(REPORTS_DIR / "evaluation_metrics.json")

	if best_model_info:
		st.metric("Best Model", str(best_model_info.get("best_model", "-")))

	if evaluation_metrics:
		st.dataframe(pd.DataFrame([evaluation_metrics]), width="stretch")

	if metrics_df is not None:
		st.subheader("Model Comparison")
		st.dataframe(metrics_df, width="stretch")
		if "ROC_AUC" in metrics_df.columns:
			st.bar_chart(metrics_df.set_index("Model")["ROC_AUC"])
	else:
		st.info("Run model training first to populate the comparison table.")

	confusion_matrix = REPORTS_DIR / "confusion_matrix.png"
	roc_curve = REPORTS_DIR / "roc_curve.png"
	precision_recall = REPORTS_DIR / "precision_recall_curve.png"
	calibration_curve = REPORTS_DIR / "calibration_curve.png"

	for title, path in (
		("Confusion Matrix", confusion_matrix),
		("ROC Curve", roc_curve),
		("Precision-Recall Curve", precision_recall),
		("Calibration Curve", calibration_curve),
	):
		if path.exists():
			st.subheader(title)
			st.image(str(path), width="stretch")


if __name__ == "__main__":
	main()
