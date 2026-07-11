"""SHAP explainability service."""

import sys
from pathlib import Path
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from ml_pipeline.src.shap_explainer import SHAPExplainer

REPORTS_DIR = Path(__file__).resolve().parents[2] / "reports"


class SHAPService:
    def __init__(self):
        self.explainer = SHAPExplainer()

    def explain(self, customer_data: dict) -> dict:
        return self.explainer.explain_single(customer_data)

    def get_feature_importance(self):
        path = REPORTS_DIR / "shap_feature_importance.csv"
        if path.exists():
            return pd.read_csv(path).to_dict(orient="records")
        return []
    
    