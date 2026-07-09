"""SHAP explainability dashboard page."""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure project root is on sys.path so `src.*` imports resolve correctly
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pandas as pd
import streamlit as st
from streamlit import runtime

from src.shap_explainer import SHAPExplainer


PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPORTS_DIR = PROJECT_ROOT / "reports"


def main() -> None:
    """Render the SHAP explainability page."""

    if not runtime.exists():
        return

    st.title("SHAP Explainability")
    st.caption("Inspect global and local feature contributions for the trained model.")

    if st.button("Generate SHAP artifacts"):
        explainer = SHAPExplainer()
        results = explainer.run()
        st.success("SHAP artifacts generated.")
        st.json({key: str(value) for key, value in results.items()})

    shap_dir = REPORTS_DIR / "shap"
    for title, filename in (
        ("Summary Plot", "summary_plot.png"),
        ("Waterfall Plot", "waterfall_plot_0.png"),
        ("Dependence Plot", "dependence_plot.png"),
    ):
        path = shap_dir / filename
        if path.exists():
            st.subheader(title)
            st.image(str(path), use_container_width=True)

    feature_importance = REPORTS_DIR / "shap_feature_importance.csv"
    if feature_importance.exists():
        st.subheader("SHAP Feature Importance")
        st.dataframe(pd.read_csv(feature_importance), use_container_width=True)


if __name__ == "__main__":
    main()
