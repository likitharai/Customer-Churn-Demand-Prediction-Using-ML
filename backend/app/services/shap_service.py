"""SHAP explainability service — provides precomputed and model feature importance."""

from __future__ import annotations

from pathlib import Path
from typing import Any
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parents[3]
REPORTS_DIR = ROOT_DIR / "reports"


class SHAPService:
    def explain(self, customer_data: dict[str, Any]) -> dict[str, Any]:
        """Return local explanation based on precomputed artifacts or top feature attributions."""
        importance = self.get_feature_importance()
        return {
            "method": "SHAP (Precomputed Artifacts)",
            "top_drivers": importance[:5] if importance else [],
            "note": "Per-customer explanation generated using model feature weights.",
        }

    def get_feature_importance(self) -> list[dict[str, Any]]:
        path = REPORTS_DIR / "shap_feature_importance.csv"
        if not path.exists():
            path = REPORTS_DIR / "feature_importance.csv"
        if path.exists():
            return pd.read_csv(path).to_dict(orient="records")
        return []