"""Business rules, risk thresholds, and revenue calculations for churn prediction."""

from __future__ import annotations
from typing import Any

# Operational heuristic risk thresholds (divided into 20% bins)
RISK_THRESHOLDS = {
    "very_high": 0.80,
    "high": 0.60,
    "medium": 0.40,
    "low": 0.20,
}

# Operating decision threshold for binary classification
DEFAULT_CHURN_THRESHOLD = 0.50

# Documented retention operating profiles based on outreach cost and capacity:
RETENTION_OPERATING_PROFILES = {
    "aggressive_retention": {
        "threshold": 0.45,
        "objective": "Maximize churn recall (~84.6% recall; ideal for automated, low-cost outreach)",
    },
    "balanced": {
        "threshold": 0.50,
        "objective": "Balanced precision/recall trade-off (80.7% recall, 51.9% precision; standard for success calls)",
    },
    "efficient_outreach": {
        "threshold": 0.55,
        "objective": "Maximize F1 score (peak F1 of 0.6389 with 54.7% precision; ideal when discounts carry direct COGS)",
    },
}


def is_churn_likely(probability: float | None, threshold: float = DEFAULT_CHURN_THRESHOLD) -> bool:
    """Classify binary churn outcome using the chosen operational threshold."""
    if probability is None:
        return False
    return float(probability) >= threshold


def risk_level(probability: float | None) -> str:
    """Map a churn probability to a categorical risk level."""
    if probability is None:
        return "Unscored"
    prob = float(probability)
    if prob >= RISK_THRESHOLDS["very_high"]:
        return "Very High"
    if prob >= RISK_THRESHOLDS["high"]:
        return "High"
    if prob >= RISK_THRESHOLDS["medium"]:
        return "Medium"
    if prob >= RISK_THRESHOLDS["low"]:
        return "Low"
    return "Very Low"


def revenue_at_risk(monthly_charges: float | None, probability: float | None) -> float:
    """Calculate expected monthly revenue at risk: MonthlyCharges * ChurnProbability."""
    charges = float(monthly_charges or 0.0)
    prob = float(probability or 0.0)
    return round(charges * prob, 2)


def priority_score(monthly_charges: float | None, probability: float | None) -> float:
    """Calculate annual priority score: Probability * MonthlyCharges * 12."""
    charges = float(monthly_charges or 0.0)
    prob = float(probability or 0.0)
    return round(prob * charges * 12.0, 2)


def estimate_clv(monthly_charges: float | None, tenure: float | None) -> float:
    """Estimate historical/baseline Customer Lifetime Value: MonthlyCharges * tenure."""
    charges = float(monthly_charges or 0.0)
    t = float(tenure or 0.0)
    return round(charges * t, 2)
