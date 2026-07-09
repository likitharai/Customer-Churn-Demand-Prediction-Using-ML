"""Executive dashboard for business leaders."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st
from streamlit import runtime


PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPORTS_DIR = PROJECT_ROOT / "reports"


def load_json(path: Path) -> dict[str, object]:
	"""Load a JSON file when present."""

	if not path.exists():
		return {}
	with path.open("r", encoding="utf-8") as file:
		return json.load(file)


def main() -> None:
	"""Render the executive dashboard page."""

	if not runtime.exists():
		return

	st.title("Executive Dashboard")
	st.caption("Revenue-at-risk and retention KPI overview.")

	kpis = load_json(REPORTS_DIR / "executive_kpis.json")

	if not kpis:
		st.info("Run the revenue-risk analysis to populate executive KPIs.")
	else:
		kpi_columns = st.columns(4)
		kpi_items = list(kpis.items())
		for column, (label, value) in zip(kpi_columns, kpi_items[:4]):
			column.metric(str(label), str(value))

	summary_path = REPORTS_DIR / "revenue_risk_summary.csv"
	if summary_path.exists():
		st.subheader("Revenue Risk Summary")
		st.dataframe(pd.read_csv(summary_path), use_container_width=True)

	segment_path = REPORTS_DIR / "revenue_risk_by_segment.csv"
	if segment_path.exists():
		st.subheader("Revenue by Segment")
		segment_df = pd.read_csv(segment_path)
		st.dataframe(segment_df, use_container_width=True)
		if "Revenue_Risk" in segment_df.columns:
			st.bar_chart(segment_df.set_index("Risk_Level")["Revenue_Risk"])

	plot_path = REPORTS_DIR / "revenue_risk_by_segment.png"
	if plot_path.exists():
		st.subheader("Revenue Risk Chart")
		st.image(str(plot_path), use_container_width=True)


if __name__ == "__main__":
	main()
