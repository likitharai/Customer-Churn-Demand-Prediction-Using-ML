import unittest

from app.api.retention_workflow import RESPONSE_ADJUSTMENTS, clamp
from app.services.operational_risk import risk_level


class RetentionRulesTests(unittest.TestCase):
    def test_positive_outcomes_reduce_risk(self):
        self.assertLess(RESPONSE_ADJUSTMENTS["offer_accepted"], 0)
        self.assertLess(RESPONSE_ADJUSTMENTS["issue_resolved"], 0)
        self.assertLess(RESPONSE_ADJUSTMENTS["customer_retained"], 0)

    def test_negative_outcomes_increase_risk(self):
        self.assertGreater(RESPONSE_ADJUSTMENTS["offer_rejected"], 0)
        self.assertGreater(RESPONSE_ADJUSTMENTS["still_cancelling"], 0)
        self.assertGreater(RESPONSE_ADJUSTMENTS["customer_churned"], 0)

    def test_probability_is_clamped_and_classified(self):
        self.assertEqual(clamp(-1), 0.01)
        self.assertEqual(clamp(2), 0.99)
        self.assertEqual(risk_level(0.85), "Very High")
        self.assertEqual(risk_level(0.25), "Low")


if __name__ == "__main__":
    unittest.main()
