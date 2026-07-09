"""
Utility Functions
"""

import pandas as pd


def print_header(title: str):

    print("=" * 70)

    print(title)

    print("=" * 70)


def missing_values(df: pd.DataFrame):

    return (
        df.isnull()
        .sum()
        .sort_values(ascending=False)
    )


def dataset_shape(df: pd.DataFrame):

    return df.shape