"""Revenue risk analytics dashboard page."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st
from streamlit import runtime

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT / "backend") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "backend"))
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import json
from app.services.business_rules import revenue_at_risk


PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPORTS_DIR = PROJECT_ROOT / "reports"


def main() -> None:
	"""Render the revenue-risk analysis page."""

	if not runtime.exists():
		return

	st.title("Revenue Risk")
	st.caption("Calculate churn-driven revenue risk and retention savings.")

	if st.button("Run revenue-risk analysis"):
		kpi_file = REPORTS_DIR / "executive_kpis.json"
		if kpi_file.exists():
			with open(kpi_file, "r", encoding="utf-8") as f:
				kpis = json.load(f)
			st.success("Revenue-risk analysis completed.")
			st.json(kpis)
		else:
			st.info("Executive KPI report not found in reports directory.")

	summary_path = REPORTS_DIR / "revenue_risk_summary.csv"
	if summary_path.exists():
		st.subheader("Revenue Risk Summary")
		st.dataframe(pd.read_csv(summary_path), width="stretch")

	high_risk_path = REPORTS_DIR / "high_risk_customers.csv"
	if high_risk_path.exists():
		st.subheader("High Risk Customers")
		st.dataframe(pd.read_csv(high_risk_path).head(25), width="stretch")

	plot_path = REPORTS_DIR / "revenue_risk_by_segment.png"
	if plot_path.exists():
		st.image(str(plot_path), width="stretch")


if __name__ == "__main__":
	main()
