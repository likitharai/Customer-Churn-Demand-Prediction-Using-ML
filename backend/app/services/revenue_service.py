"""Revenue risk service."""

import json
from pathlib import Path
import pandas as pd

REPORTS_DIR = Path(__file__).resolve().parents[2] / "reports"


class RevenueService:
    def get_executive_kpis(self) -> dict:
        path = REPORTS_DIR / "executive_kpis.json"
        if path.exists():
            return json.loads(path.read_text())
        return {}

    def get_revenue_risk_summary(self):
        path = REPORTS_DIR / "revenue_risk_summary.csv"
        if path.exists():
            return pd.read_csv(path).to_dict(orient="records")
        return []

    def get_high_risk_customers(self):
        path = REPORTS_DIR / "high_risk_customers.csv"
        if path.exists():
            return pd.read_csv(path).head(100).to_dict(orient="records")
        return []

    def get_churn_by_segment(self):
        path = REPORTS_DIR / "revenue_risk_by_segment.csv"
        if path.exists():
            return pd.read_csv(path).to_dict(orient="records")
        return []
