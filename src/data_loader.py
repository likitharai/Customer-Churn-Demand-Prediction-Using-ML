"""
Project      : Decision Intelligence Platform
Module       : data_loader.py
Author       : Likitha Rai

Description:
Loads, validates and cleans the Telco Customer Churn dataset.
"""

from pathlib import Path

import pandas as pd

from src.config import RAW_DATA_DIR, PROCESSED_DATA_DIR
from src.logger import logger


class DataLoader:

    def __init__(self):

        self.input_file = RAW_DATA_DIR / "telco_churn.csv"

        self.output_file = PROCESSED_DATA_DIR / "cleaned_telco.csv"

    # ==========================================================
    # Load Dataset
    # ==========================================================

    def load_dataset(self) -> pd.DataFrame:

        logger.info("Loading dataset...")

        df = pd.read_csv(self.input_file)

        logger.info(f"Dataset Loaded : {df.shape}")

        return df

    # ==========================================================
    # Dataset Summary
    # ==========================================================

    @staticmethod
    def dataset_summary(df):

        print("\n================ Dataset Summary ================\n")

        print(df.info())

        print("\nShape")

        print(df.shape)

        print("\nColumns")

        print(df.columns.tolist())

    # ==========================================================
    # Missing Values
    # ==========================================================

    @staticmethod
    def missing_values(df):

        missing = pd.DataFrame({

            "Missing Values": df.isnull().sum(),

            "Percentage": round(

                df.isnull().mean() * 100,

                2

            )

        })

        missing = missing[missing["Missing Values"] > 0]

        print("\nMissing Values")

        print(missing)

        return missing

    # ==========================================================
    # Duplicate Records
    # ==========================================================

    @staticmethod
    def remove_duplicates(df):

        before = len(df)

        df = df.drop_duplicates()

        after = len(df)

        logger.info(f"Duplicates Removed : {before-after}")

        return df

    # ==========================================================
    # Convert TotalCharges
    # ==========================================================

    @staticmethod
    def convert_total_charges(df):

        df["TotalCharges"] = pd.to_numeric(

            df["TotalCharges"],

            errors="coerce"

        )

        df["TotalCharges"] = df["TotalCharges"].fillna(

            df["TotalCharges"].median()

        )

        return df

    # ==========================================================
    # Clean Categorical Columns
    # ==========================================================

    @staticmethod
    def clean_categorical_columns(df):

        columns = [

            "SeniorCitizen",

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

            "Churn"

        ]

        replacements = {

            "True": "Yes",

            "False": "No",

            "1": "Yes",

            "0": "No",

            "No internet service": "No",

            "No phone service": "No"

        }

        for col in columns:

            if col in df.columns:

                df[col] = df[col].replace(replacements)

        return df

    # ==========================================================
    # Validate Numeric Columns
    # ==========================================================

    @staticmethod
    def validate_numeric_columns(df):

        numeric_columns = df.select_dtypes(

            include=["number"]

        ).columns

        for col in numeric_columns:

            invalid = df[df[col] < 0]

            if not invalid.empty:

                logger.warning(

                    f"{len(invalid)} invalid values found in {col}"

                )

    # ==========================================================
    # Target Column
    # ==========================================================

    @staticmethod
    def create_target(df):

        df["Churn_flag"] = df["Churn"].map({

            "Yes": 1,

            "No": 0

        })

        return df
    
        # Remove unwanted columns
        drop_columns = ["Unnamed: 0"]

        for col in drop_columns:
            if col in df.columns:
                df.drop(columns=col, inplace=True)

    # ==========================================================
    # Save Dataset
    # ==========================================================

    def save_dataset(self, df):

        PROCESSED_DATA_DIR.mkdir(

            parents=True,

            exist_ok=True

        )

        df.to_csv(

            self.output_file,

            index=False

        )

        logger.info(

            f"Clean Dataset Saved : {self.output_file}"

        )

    # ==========================================================
    # Complete Pipeline
    # ==========================================================

    def run(self):

        df = self.load_dataset()

        self.dataset_summary(df)

        self.missing_values(df)

        df = self.remove_duplicates(df)

        df = self.convert_total_charges(df)

        df = self.clean_categorical_columns(df)

        self.validate_numeric_columns(df)

        df = self.create_target(df)

        self.save_dataset(df)

        print("\nDataset preprocessing completed successfully.")

        return df


if __name__ == "__main__":

    loader = DataLoader()

    cleaned_df = loader.run()

    print(cleaned_df.head())