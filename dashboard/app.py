"""Streamlit entrypoint for the decision intelligence platform home page."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def load_json(path: Path) -> dict[str, object]:
    """Load a JSON file if it exists."""

    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def load_dataframe(path: Path) -> pd.DataFrame | None:
    """Load a CSV file if it exists."""

    if not path.exists():
        return None
    return pd.read_csv(path)


def metric_card(label: str, value: str) -> None:
    """Render a small KPI card using Streamlit markdown."""

    st.markdown(
        f"""
        <div style="padding: 1rem; border-radius: 1rem; background: linear-gradient(135deg, #0f172a, #1e293b); color: white;">
            <div style="font-size: 0.85rem; opacity: 0.75; text-transform: uppercase; letter-spacing: 0.08em;">{label}</div>
            <div style="font-size: 1.6rem; font-weight: 700; margin-top: 0.35rem;">{value}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def main() -> None:
    """Render the platform home page."""

    st.set_page_config(page_title="Decision Intelligence Platform", layout="wide")
    st.markdown(
        """
        <style>
        .hero {
            padding: 2rem;
            border-radius: 1.5rem;
            background: linear-gradient(135deg, #07111f 0%, #0f766e 55%, #134e4a 100%);
            color: white;
        }
        .hero h1 { margin-bottom: 0.25rem; }
        .hero p { margin-top: 0; opacity: 0.85; font-size: 1.05rem; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="hero">
            <h1>Decision Intelligence Platform</h1>
            <p>Enterprise churn prediction, revenue risk analysis, explainability, and retention actions in one workflow.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    left, middle, right = st.columns(3)
    metrics = load_json(PROJECT_ROOT / "reports" / "executive_kpis.json")
    model_info = load_json(PROJECT_ROOT / "models" / "best_model_info.json")
    evaluation_metrics = load_json(PROJECT_ROOT / "reports" / "evaluation_metrics.json")

    with left:
        metric_card("Total Customers", str(metrics.get("Total Customers", "-")))
    with middle:
        metric_card("Revenue At Risk", str(metrics.get("Revenue At Risk", "-")))
    with right:
        metric_card("Best Model", str(model_info.get("best_model", "-")))

    st.write("")
    performance, business = st.columns(2)

    with performance:
        st.subheader("Model Snapshot")
        if evaluation_metrics:
            perf_df = pd.DataFrame([evaluation_metrics])
            st.dataframe(perf_df, width="stretch")
        else:
            st.info("Run training and evaluation to populate model metrics.")

    with business:
        st.subheader("Business Snapshot")
        if metrics:
            st.dataframe(pd.DataFrame([metrics]), width="stretch")
        else:
            st.info("Run revenue-risk analysis to populate executive KPIs.")

    st.subheader("Operational Artifacts")
    artifact_table = pd.DataFrame(
        [
            {"Artifact": "Best Model", "Path": "models/best_model.pkl"},
            {"Artifact": "Model Metrics", "Path": "models/model_metrics.csv"},
            {"Artifact": "Evaluation Metrics", "Path": "reports/evaluation_metrics.json"},
            {"Artifact": "Revenue Risk Summary", "Path": "reports/revenue_risk_summary.csv"},
            {"Artifact": "SHAP Feature Importance", "Path": "reports/shap_feature_importance.csv"},
        ]
    )
    st.dataframe(artifact_table, width="stretch", hide_index=True)

    st.subheader("Dataset Preview")
    cleaned_data = load_dataframe(PROJECT_ROOT / "Data" / "processed" / "cleaned_telco.csv")
    if cleaned_data is not None:
        st.dataframe(cleaned_data.head(10), width="stretch")
    else:
        st.info("Cleaned dataset not found yet.")


if __name__ == "__main__":
    main()
