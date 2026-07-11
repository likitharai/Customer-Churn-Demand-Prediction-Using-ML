"""Load and clean the raw Telco churn dataset."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from ml_pipeline.src.config import PROCESSED_DATA_DIR, RAW_DATA_DIR
from ml_pipeline.src.constants import TARGET_COLUMN, TARGET_LABEL_COLUMN
from ml_pipeline.src.logger import logger


class DataLoader:
    """Load, validate, and standardize the raw churn dataset."""

    def __init__(
        self,
        input_file: Path | None = None,
        output_file: Path | None = None,
    ) -> None:
        self.input_file = input_file or (RAW_DATA_DIR / "telco_churn.csv")
        self.output_file = output_file or (PROCESSED_DATA_DIR / "cleaned_telco.csv")

    def load_dataset(self) -> pd.DataFrame:
        """Load the raw dataset from disk."""

        if not self.input_file.exists():
            raise FileNotFoundError(f"Raw dataset not found: {self.input_file}")

        logger.info("Loading raw churn dataset from %s", self.input_file)
        return pd.read_csv(self.input_file)

    @staticmethod
    def dataset_summary(df: pd.DataFrame) -> dict[str, Any]:
        """Return a compact summary of the dataset."""

        summary = {
            "shape": df.shape,
            "columns": df.columns.tolist(),
            "dtypes": df.dtypes.astype(str).to_dict(),
            "missing_values": df.isna().sum().to_dict(),
        }
        logger.info("Dataset summary: %s", summary)
        return summary

    @staticmethod
    def remove_duplicates(df: pd.DataFrame) -> pd.DataFrame:
        """Remove duplicate rows and log how many were dropped."""

        before = len(df)
        cleaned_df = df.drop_duplicates().copy()
        logger.info("Removed %s duplicate rows", before - len(cleaned_df))
        return cleaned_df

    @staticmethod
    def convert_total_charges(df: pd.DataFrame) -> pd.DataFrame:
        """Convert the TotalCharges column to numeric and impute missing values."""

        cleaned_df = df.copy()
        if "TotalCharges" in cleaned_df.columns:
            cleaned_df["TotalCharges"] = pd.to_numeric(
                cleaned_df["TotalCharges"],
                errors="coerce",
            )
            cleaned_df["TotalCharges"] = cleaned_df["TotalCharges"].fillna(
                cleaned_df["TotalCharges"].median(),
            )
        return cleaned_df

    @staticmethod
    def clean_categorical_columns(df: pd.DataFrame) -> pd.DataFrame:
        """Normalize categorical values to a consistent representation."""

        cleaned_df = df.copy()

        object_columns = cleaned_df.select_dtypes(include=["object"]).columns
        for column in object_columns:
            cleaned_df[column] = cleaned_df[column].apply(
                lambda value: value.strip() if isinstance(value, str) else value
            )

        replacements = {
            "True": "Yes",
            "False": "No",
            "1": "Yes",
            "0": "No",
            "No internet service": "No",
            "No phone service": "No",
        }

        categorical_columns = [
            "Partner",
            "Dependents",
            "PhoneService",
            "MultipleLines",
            "OnlineSecurity",
            "OnlineBackup",
            "DeviceProtection",
            "TechSupport",
            "StreamingTV",
            "StreamingMovies",
            "PaperlessBilling",
            TARGET_LABEL_COLUMN,
        ]

        for column in categorical_columns:
            if column in cleaned_df.columns:
                cleaned_df[column] = cleaned_df[column].replace(replacements)

        return cleaned_df

    @staticmethod
    def validate_numeric_columns(df: pd.DataFrame) -> None:
        """Log negative values in numeric columns if present."""

        for column in df.select_dtypes(include=["number"]).columns:
            invalid_rows = df[df[column] < 0]
            if not invalid_rows.empty:
                logger.warning(
                    "Found %s negative values in %s",
                    len(invalid_rows),
                    column,
                )

    @staticmethod
    def create_target(df: pd.DataFrame) -> pd.DataFrame:
        """Create the binary churn flag used for model training."""

        if TARGET_LABEL_COLUMN not in df.columns:
            raise KeyError(f"Missing target label column: {TARGET_LABEL_COLUMN}")

        cleaned_df = df.copy()

        target_series = cleaned_df[TARGET_LABEL_COLUMN]
        missing_target_rows = target_series.isna() | target_series.astype(str).str.strip().isin(["", "nan", "none"])
        if missing_target_rows.any():
            logger.warning("Dropping %s rows with missing churn labels", int(missing_target_rows.sum()))
            cleaned_df = cleaned_df.loc[~missing_target_rows].copy()
            target_series = cleaned_df[TARGET_LABEL_COLUMN]

        raw_target = target_series.astype(str).str.strip().str.lower()
        cleaned_df[TARGET_COLUMN] = raw_target.map({"yes": 1, "no": 0})

        invalid_rows = cleaned_df[TARGET_COLUMN].isna()
        if invalid_rows.any():
            bad_values = raw_target.loc[invalid_rows].dropna().unique().tolist()
            raise ValueError(f"Unable to derive churn target from raw labels: {bad_values}")

        cleaned_df[TARGET_COLUMN] = cleaned_df[TARGET_COLUMN].astype(int)

        drop_columns = [column for column in ("Unnamed: 0",) if column in cleaned_df.columns]
        if drop_columns:
            cleaned_df = cleaned_df.drop(columns=drop_columns)

        return cleaned_df
    def save_dataset(self, df: pd.DataFrame) -> None:
        """Persist the cleaned dataset to the processed directory."""

        PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
        df.to_csv(self.output_file, index=False)
        logger.info("Saved cleaned dataset to %s", self.output_file)

    def run(self) -> pd.DataFrame:
        """Execute the full cleaning workflow."""

        try:
            df = self.load_dataset()
            self.dataset_summary(df)
            df = self.remove_duplicates(df)
            df = self.convert_total_charges(df)
            df = self.clean_categorical_columns(df)
            self.validate_numeric_columns(df)
            df = self.create_target(df)
            self.save_dataset(df)
            logger.info("Dataset preprocessing completed successfully")
            return df
        except Exception as exc:
            logger.exception("Failed to clean the raw dataset")
            raise RuntimeError("Dataset cleaning failed") from exc


if __name__ == "__main__":
    loader = DataLoader()
    cleaned_df = loader.run()
    print(cleaned_df.head())