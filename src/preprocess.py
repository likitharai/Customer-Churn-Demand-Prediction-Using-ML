"""
Project      : Decision Intelligence Platform
Module       : preprocess.py
Author       : Likitha Rai

Description:
Data preprocessing pipeline using ColumnTransformer and
OneHotEncoder for production-ready ML.
"""

import joblib
import pandas as pd

from imblearn.over_sampling import SMOTE

from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from src.config import (
    PROCESSED_DATA_DIR,
    RESAMPLED_DATA_DIR,
    MODELS_DIR,
)

from src.constants import (
    RANDOM_STATE,
    TEST_SIZE,
    TARGET_COLUMN,
)

from src.logger import logger


class Preprocessor:

    def __init__(self):

        self.input_file = (
            PROCESSED_DATA_DIR /
            "cleaned_telco.csv"
        )

        self.pipeline = None

        self.feature_names = None

    # =====================================================
    # Load Dataset
    # =====================================================

    def load_dataset(self):

        logger.info("Loading cleaned dataset...")

        df = pd.read_csv(self.input_file)

        # Remove unnecessary columns
        drop_cols = [
            "Unnamed: 0",
            "customerID",
        ]

        for col in drop_cols:

            if col in df.columns:

                df.drop(
                    columns=col,
                    inplace=True,
                )

        df[TARGET_COLUMN] = (
            pd.to_numeric(
                df[TARGET_COLUMN],
                errors="coerce",
            )
        )

        df.dropna(
            subset=[TARGET_COLUMN],
            inplace=True,
        )

        df[TARGET_COLUMN] = (
            df[TARGET_COLUMN]
            .astype(int)
        )

        logger.info(
            f"Dataset Shape : {df.shape}"
        )

        return df

    # =====================================================
    # Feature / Target
    # =====================================================

    def split_xy(self, df):

        X = df.drop(
            columns=[
                TARGET_COLUMN,
                "Churn",
            ],
            errors="ignore",
        )

        y = df[TARGET_COLUMN]

        return X, y

    # =====================================================
    # Build Pipeline
    # =====================================================

    def build_pipeline(self, X):

        numeric_features = X.select_dtypes(
            include=[
                "int64",
                "float64",
            ]
        ).columns.tolist()

        categorical_features = X.select_dtypes(
            include=[
                "object",
                "category",
            ]
        ).columns.tolist()

        numeric_pipeline = Pipeline(

            steps=[

                (
                    "imputer",

                    SimpleImputer(
                        strategy="median"
                    ),

                ),

                (
                    "scaler",

                    StandardScaler(),

                ),

            ]

        )

        categorical_pipeline = Pipeline(

            steps=[

                (
                    "imputer",

                    SimpleImputer(
                        strategy="most_frequent"
                    ),

                ),

                (
                    "encoder",

                    OneHotEncoder(
                        handle_unknown="ignore",
                        sparse_output=False,
                    ),

                ),

            ]

        )

        self.pipeline = ColumnTransformer(

            transformers=[

                (
                    "numeric",

                    numeric_pipeline,

                    numeric_features,

                ),

                (
                    "categorical",

                    categorical_pipeline,

                    categorical_features,

                ),

            ]

        )

        logger.info(
            "Preprocessing pipeline created."
        )

        return self.pipeline
    
    # =====================================================
    # Fit & Transform Dataset
    # =====================================================

    def preprocess_dataset(self, X):

        logger.info("Fitting preprocessing pipeline...")

        X_processed = self.pipeline.fit_transform(X)

        # Feature names after OneHotEncoding
        self.feature_names = self.pipeline.get_feature_names_out()

        X_processed = pd.DataFrame(
            X_processed,
            columns=self.feature_names,
            index=X.index,
        )

        logger.info(
            f"Processed Feature Shape : {X_processed.shape}"
        )

        return X_processed

    # =====================================================
    # Train Test Split
    # =====================================================

    def split_dataset(self, X, y):

        logger.info("Splitting dataset...")

        X_train, X_test, y_train, y_test = train_test_split(

            X,

            y,

            test_size=TEST_SIZE,

            random_state=RANDOM_STATE,

            stratify=y,

        )

        logger.info(
            f"Train : {X_train.shape}"
        )

        logger.info(
            f"Test  : {X_test.shape}"
        )

        return (

            X_train,

            X_test,

            y_train,

            y_test,

        )

    # =====================================================
    # Apply SMOTE
    # =====================================================

    def apply_smote(

        self,

        X_train,

        y_train,

    ):

        logger.info("Applying SMOTE...")

        smote = SMOTE(
            random_state=RANDOM_STATE
        )

        X_train_resampled, y_train_resampled = (

            smote.fit_resample(

                X_train,

                y_train,

            )

        )

        logger.info(
            f"Resampled Shape : {X_train_resampled.shape}"
        )

        return (

            X_train_resampled,

            y_train_resampled,

        )

    # =====================================================
    # Save Processed Dataset
    # =====================================================

    def save_processed_dataset(

        self,

        X_train,

        X_test,

        y_train,

        y_test,

    ):

        PROCESSED_DATA_DIR.mkdir(

            parents=True,

            exist_ok=True,

        )

        X_train.to_csv(

            PROCESSED_DATA_DIR /

            "x_train.csv",

            index=False,

        )

        X_test.to_csv(

            PROCESSED_DATA_DIR /

            "x_test.csv",

            index=False,

        )

        y_train.to_frame(

            TARGET_COLUMN

        ).to_csv(

            PROCESSED_DATA_DIR /

            "y_train.csv",

            index=False,

        )

        y_test.to_frame(

            TARGET_COLUMN

        ).to_csv(

            PROCESSED_DATA_DIR /

            "y_test.csv",

            index=False,

        )

        logger.info(
            "Processed datasets saved."
        )

    # =====================================================
    # Save Resampled Dataset
    # =====================================================

    def save_resampled_dataset(

        self,

        X_train_resampled,

        y_train_resampled,

        X_test,

        y_test,

    ):

        RESAMPLED_DATA_DIR.mkdir(

            parents=True,

            exist_ok=True,

        )

        X_train_resampled.to_csv(

            RESAMPLED_DATA_DIR /

            "x_train_resampled.csv",

            index=False,

        )

        X_test.to_csv(

            RESAMPLED_DATA_DIR /

            "x_test_resampled.csv",

            index=False,

        )

        y_train_resampled.to_frame(

            TARGET_COLUMN

        ).to_csv(

            RESAMPLED_DATA_DIR /

            "y_train_resampled.csv",

            index=False,

        )

        y_test.to_frame(

            TARGET_COLUMN

        ).to_csv(

            RESAMPLED_DATA_DIR /

            "y_test_resampled.csv",

            index=False,

        )

        logger.info(
            "Resampled datasets saved."
        )

    # =====================================================
    # Process Dataset
    # =====================================================

    def process(self):

        df = self.load_dataset()

        X, y = self.split_xy(df)

        self.build_pipeline(X)

        X = self.preprocess_dataset(X)

        (

            X_train,

            X_test,

            y_train,

            y_test,

        ) = self.split_dataset(

            X,

            y,

        )

        (

            X_train_resampled,

            y_train_resampled,

        ) = self.apply_smote(

            X_train,

            y_train,

        )

        self.save_processed_dataset(

            X_train,

            X_test,

            y_train,

            y_test,

        )

        self.save_resampled_dataset(

            X_train_resampled,

            y_train_resampled,

            X_test,

            y_test,

        )

        return (

            X_train,

            X_test,

            y_train,

            y_test,

            X_train_resampled,

            y_train_resampled,

        )

    # =====================================================
    # Save Preprocessing Pipeline
    # =====================================================

    def save_pipeline(self):

        MODELS_DIR.mkdir(
            parents=True,
            exist_ok=True,
        )

        pipeline_path = (
            MODELS_DIR /
            "preprocessing_pipeline.pkl"
        )

        joblib.dump(
            self.pipeline,
            pipeline_path,
        )

        logger.info(
            f"Pipeline Saved : {pipeline_path}"
        )

    # =====================================================
    # Save Feature Columns
    # =====================================================

    def save_feature_columns(self):

        feature_path = (
            MODELS_DIR /
            "feature_columns.pkl"
        )

        joblib.dump(
            list(self.feature_names),
            feature_path,
        )

        logger.info(
            f"Feature Columns Saved : {feature_path}"
        )

    # =====================================================
    # Display Summary
    # =====================================================

    @staticmethod
    def display_summary():

        print("\n")
        print("=" * 70)
        print("PREPROCESSING COMPLETED SUCCESSFULLY")
        print("=" * 70)

        print("\nGenerated Files\n")

        print("data/processed/")
        print("   x_train.csv")
        print("   x_test.csv")
        print("   y_train.csv")
        print("   y_test.csv")

        print("\n")

        print("data/resampled/")
        print("   x_train_resampled.csv")
        print("   x_test_resampled.csv")
        print("   y_train_resampled.csv")
        print("   y_test_resampled.csv")

        print("\n")

        print("models/")
        print("   preprocessing_pipeline.pkl")
        print("   feature_columns.pkl")

        print("=" * 70)

    # =====================================================
    # Run
    # =====================================================

    def run(self):

        (
            X_train,
            X_test,
            y_train,
            y_test,
            X_train_resampled,
            y_train_resampled,
        ) = self.process()

        self.save_pipeline()

        self.save_feature_columns()

        self.display_summary()

        return {

            "X_train": X_train,

            "X_test": X_test,

            "y_train": y_train,

            "y_test": y_test,

            "X_train_resampled": X_train_resampled,

            "y_train_resampled": y_train_resampled,

        }


# =====================================================
# Main
# =====================================================

if __name__ == "__main__":

    processor = Preprocessor()

    processor.run()    