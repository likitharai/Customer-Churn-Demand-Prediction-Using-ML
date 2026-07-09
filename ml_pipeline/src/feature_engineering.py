"""Feature engineering module."""

from __future__ import annotations

import pandas as pd


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """Create derived features from raw telecom data."""
    df = df.copy()

    # Tenure buckets
    df["tenure_group"] = pd.cut(
        df["tenure"],
        bins=[0, 12, 24, 48, 72],
        labels=["0-1yr", "1-2yr", "2-4yr", "4+yr"],
    )

    # Charge per month ratio
    df["charge_per_tenure"] = df["MonthlyCharges"] / (df["tenure"] + 1)

    # Service count
    service_cols = ["PhoneService", "OnlineSecurity", "OnlineBackup",
                    "DeviceProtection", "TechSupport", "StreamingTV", "StreamingMovies"]
    df["service_count"] = df[service_cols].apply(lambda row: (row == "Yes").sum(), axis=1)

    return df
