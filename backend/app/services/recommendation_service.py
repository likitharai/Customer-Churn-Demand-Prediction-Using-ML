"""Recommendation service."""

import sys
from pathlib import Path
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from ml_pipeline.src.recommendation_engine import RecommendationEngine


class RecommendationService:
    def __init__(self):
        self.engine = RecommendationEngine()

    def generate(self, customer_data: dict) -> list:
        df = pd.DataFrame([customer_data])
        result = self.engine.generate_recommendations(df)
        return result.to_dict(orient="records")
