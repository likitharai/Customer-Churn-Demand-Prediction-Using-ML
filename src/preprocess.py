"""Train/test split and preprocessing pipeline for churn modeling."""

from __future__ import annotations

from pathlib import Path

import joblib
import pandas as pd
from imblearn.over_sampling import SMOTE
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from src.config import MODELS_DIR, PROCESSED_DATA_DIR, RESAMPLED_DATA_DIR
from src.constants import RANDOM_STATE, TARGET_COLUMN, TEST_SIZE
from src.logger import logger


class Preprocessor:
    """Create train/test splits and a reusable preprocessing pipeline."""

    def __init__(self, input_file: Path | None = None) -> None:
        self.input_file = input_file or (PROCESSED_DATA_DIR / "cleaned_telco.csv")
        self.pipeline: ColumnTransformer | None = None
        self.feature_names: list[str] | None = None

    def load_dataset(self) -> pd.DataFrame:
        """Load the cleaned dataset prepared by the data loader."""

        if not self.input_file.exists():
            raise FileNotFoundError(f"Cleaned dataset not found: {self.input_file}")

        logger.info("Loading cleaned dataset from %s", self.input_file)
        df = pd.read_csv(self.input_file)

        for column in ("Unnamed: 0", "customerID"):
            if column in df.columns:
                df = df.drop(columns=column)

        if TARGET_COLUMN not in df.columns:
            raise KeyError(f"Missing target column: {TARGET_COLUMN}")

        df[TARGET_COLUMN] = pd.to_numeric(df[TARGET_COLUMN], errors="coerce")
        df = df.dropna(subset=[TARGET_COLUMN]).copy()
        df[TARGET_COLUMN] = df[TARGET_COLUMN].astype(int)

        logger.info("Loaded dataset shape: %s", df.shape)
        return df

    @staticmethod
    def split_xy(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
        """Split the target column from the feature matrix."""

        X = df.drop(columns=[TARGET_COLUMN, "Churn"], errors="ignore")
        y = df[TARGET_COLUMN]
        return X, y

    def split_dataset(
        self,
        X: pd.DataFrame,
        y: pd.Series,
    ) -> tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
        """Create stratified train and test splits."""

        X_train, X_test, y_train, y_test = train_test_split(
            X,
            y,
            test_size=TEST_SIZE,
            random_state=RANDOM_STATE,
            stratify=y,
        )

        logger.info("Train shape: %s | Test shape: %s", X_train.shape, X_test.shape)
        return X_train, X_test, y_train, y_test

    def build_pipeline(self, X: pd.DataFrame) -> ColumnTransformer:
        """Build a preprocessing pipeline for numeric and categorical features."""

        numeric_features = X.select_dtypes(include=["number", "bool"]).columns.tolist()
        categorical_features = X.select_dtypes(include=["object", "category"]).columns.tolist()

        numeric_pipeline = Pipeline(
            steps=[
                ("imputer", SimpleImputer(strategy="median")),
                ("scaler", StandardScaler()),
            ]
        )

        categorical_pipeline = Pipeline(
            steps=[
                ("imputer", SimpleImputer(strategy="most_frequent")),
                (
                    "encoder",
                    OneHotEncoder(handle_unknown="ignore", sparse_output=False),
                ),
            ]
        )

        self.pipeline = ColumnTransformer(
            transformers=[
                ("numeric", numeric_pipeline, numeric_features),
                ("categorical", categorical_pipeline, categorical_features),
            ]
        )
        logger.info("Preprocessing pipeline created")
        return self.pipeline

    def fit_transform_features(self, X_train: pd.DataFrame, X_test: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
        """Fit the pipeline on training data and transform both splits."""

        if self.pipeline is None:
            self.build_pipeline(X_train)

        logger.info("Fitting preprocessing pipeline on training data")
        X_train_processed = self.pipeline.fit_transform(X_train)
        X_test_processed = self.pipeline.transform(X_test)

        self.feature_names = self._get_feature_names()

        X_train_df = pd.DataFrame(X_train_processed, columns=self.feature_names, index=X_train.index)
        X_test_df = pd.DataFrame(X_test_processed, columns=self.feature_names, index=X_test.index)

        logger.info("Processed train shape: %s | processed test shape: %s", X_train_df.shape, X_test_df.shape)
        return X_train_df, X_test_df

    def _get_feature_names(self) -> list[str]:
        """Extract feature names from the fitted column transformer."""

        if self.pipeline is None:
            raise RuntimeError("Pipeline has not been fitted yet")

        feature_names = self.pipeline.get_feature_names_out()
        return [str(feature_name) for feature_name in feature_names]

    @staticmethod
    def apply_smote(
        X_train: pd.DataFrame,
        y_train: pd.Series,
    ) -> tuple[pd.DataFrame, pd.Series]:
        """Balance the training data using SMOTE."""

        smote = SMOTE(random_state=RANDOM_STATE)
        X_resampled, y_resampled = smote.fit_resample(X_train, y_train)
        X_resampled_df = pd.DataFrame(X_resampled, columns=X_train.columns)
        y_resampled_series = pd.Series(y_resampled, name=TARGET_COLUMN)
        logger.info("Resampled training shape: %s", X_resampled_df.shape)
        return X_resampled_df, y_resampled_series

    @staticmethod
    def save_dataframe(df: pd.DataFrame, path: Path) -> None:
        """Persist a dataframe to disk with logging."""

        path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(path, index=False)

    def save_processed_dataset(
        self,
        X_train: pd.DataFrame,
        X_test: pd.DataFrame,
        y_train: pd.Series,
        y_test: pd.Series,
    ) -> None:
        """Save the transformed train and test splits."""

        PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.save_dataframe(X_train, PROCESSED_DATA_DIR / "x_train.csv")
        self.save_dataframe(X_test, PROCESSED_DATA_DIR / "x_test.csv")
        self.save_dataframe(y_train.to_frame(name=TARGET_COLUMN), PROCESSED_DATA_DIR / "y_train.csv")
        self.save_dataframe(y_test.to_frame(name=TARGET_COLUMN), PROCESSED_DATA_DIR / "y_test.csv")
        logger.info("Saved processed datasets to %s", PROCESSED_DATA_DIR)

    def save_resampled_dataset(
        self,
        X_train_resampled: pd.DataFrame,
        y_train_resampled: pd.Series,
        X_test: pd.DataFrame,
        y_test: pd.Series,
    ) -> None:
        """Save the resampled training data alongside the untouched test split."""

        RESAMPLED_DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.save_dataframe(X_train_resampled, RESAMPLED_DATA_DIR / "x_train_resampled.csv")
        self.save_dataframe(X_test, RESAMPLED_DATA_DIR / "x_test_resampled.csv")
        self.save_dataframe(y_train_resampled.to_frame(name=TARGET_COLUMN), RESAMPLED_DATA_DIR / "y_train_resampled.csv")
        self.save_dataframe(y_test.to_frame(name=TARGET_COLUMN), RESAMPLED_DATA_DIR / "y_test_resampled.csv")
        logger.info("Saved resampled datasets to %s", RESAMPLED_DATA_DIR)

    def save_pipeline(self) -> None:
        """Persist the fitted preprocessing pipeline."""

        if self.pipeline is None:
            raise RuntimeError("Pipeline is not available for saving")

        MODELS_DIR.mkdir(parents=True, exist_ok=True)
        joblib.dump(self.pipeline, MODELS_DIR / "preprocessing_pipeline.pkl")
        logger.info("Saved preprocessing pipeline")

    def save_feature_columns(self) -> None:
        """Persist the transformed feature column names."""

        if self.feature_names is None:
            raise RuntimeError("Feature names are not available for saving")

        joblib.dump(self.feature_names, MODELS_DIR / "feature_columns.pkl")
        logger.info("Saved %s feature names", len(self.feature_names))

    def process(self) -> tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series, pd.DataFrame, pd.Series]:
        """Run the full preprocessing workflow."""

        df = self.load_dataset()
        X, y = self.split_xy(df)
        X_train_raw, X_test_raw, y_train, y_test = self.split_dataset(X, y)
        X_train_processed, X_test_processed = self.fit_transform_features(X_train_raw, X_test_raw)
        X_train_resampled, y_train_resampled = self.apply_smote(X_train_processed, y_train)
        self.save_processed_dataset(X_train_processed, X_test_processed, y_train, y_test)
        self.save_resampled_dataset(X_train_resampled, y_train_resampled, X_test_processed, y_test)
        return X_train_processed, X_test_processed, y_train, y_test, X_train_resampled, y_train_resampled

    def run(self) -> dict[str, pd.DataFrame | pd.Series]:
        """Execute preprocessing and persist all derived artifacts."""

        try:
            X_train, X_test, y_train, y_test, X_train_resampled, y_train_resampled = self.process()
            self.save_pipeline()
            self.save_feature_columns()
            logger.info("Preprocessing completed successfully")
            return {
                "X_train": X_train,
                "X_test": X_test,
                "y_train": y_train,
                "y_test": y_test,
                "X_train_resampled": X_train_resampled,
                "y_train_resampled": y_train_resampled,
            }
        except Exception as exc:
            logger.exception("Preprocessing failed")
            raise RuntimeError("Preprocessing pipeline failed") from exc


if __name__ == "__main__":
    processor = Preprocessor()
    processor.run()
