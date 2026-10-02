"""Unit tests for business rules, risk thresholds, and revenue-at-risk calculations."""

from __future__ import annotations

import pytest
from app.services.business_rules import (
    RISK_THRESHOLDS,
    estimate_clv,
    priority_score,
    revenue_at_risk,
    risk_level,
)


class TestRiskThresholds:
    def test_risk_level_boundaries(self):
        assert risk_level(None) == "Unscored"
        assert risk_level(0.0) == "Very Low"
        assert risk_level(0.19) == "Very Low"
        assert risk_level(0.20) == "Low"
        assert risk_level(0.39) == "Low"
        assert risk_level(0.40) == "Medium"
        assert risk_level(0.59) == "Medium"
        assert risk_level(0.60) == "High"
        assert risk_level(0.79) == "High"
        assert risk_level(0.80) == "Very High"
        assert risk_level(1.0) == "Very High"

    def test_risk_threshold_constants(self):
        assert RISK_THRESHOLDS["very_high"] == 0.80
        assert RISK_THRESHOLDS["high"] == 0.60
        assert RISK_THRESHOLDS["medium"] == 0.40
        assert RISK_THRESHOLDS["low"] == 0.20

    def test_decision_thresholds_and_profiles(self):
        from app.services.business_rules import DEFAULT_CHURN_THRESHOLD, RETENTION_OPERATING_PROFILES, is_churn_likely

        assert DEFAULT_CHURN_THRESHOLD == 0.50
        assert is_churn_likely(0.51) is True
        assert is_churn_likely(0.49) is False
        assert is_churn_likely(None) is False

        # Configurable threshold
        assert is_churn_likely(0.46, threshold=0.45) is True
        assert is_churn_likely(0.44, threshold=0.45) is False

        # Profiles presence
        assert "aggressive_retention" in RETENTION_OPERATING_PROFILES
        assert "balanced" in RETENTION_OPERATING_PROFILES
        assert "efficient_outreach" in RETENTION_OPERATING_PROFILES


class TestRevenueCalculations:
    def test_revenue_at_risk_basic(self):
        # 100.0 * 0.5 = 50.0
        assert revenue_at_risk(100.0, 0.5) == 50.0

    def test_revenue_at_risk_rounding(self):
        # 79.99 * 0.333 = 26.63667 -> 26.64
        assert revenue_at_risk(79.99, 0.333) == 26.64

    def test_revenue_at_risk_null_and_zero(self):
        assert revenue_at_risk(None, 0.5) == 0.0
        assert revenue_at_risk(100.0, None) == 0.0
        assert revenue_at_risk(0.0, 0.8) == 0.0
        assert revenue_at_risk(100.0, 0.0) == 0.0

    def test_priority_score_annualized(self):
        # 0.5 * 100.0 * 12 = 600.0
        assert priority_score(100.0, 0.5) == 600.0
        assert priority_score(None, 0.5) == 0.0
        assert priority_score(100.0, None) == 0.0

    def test_estimate_clv(self):
        # 80.0 * 24 = 1920.0
        assert estimate_clv(80.0, 24) == 1920.0
        assert estimate_clv(None, 24) == 0.0
        assert estimate_clv(80.0, None) == 0.0
