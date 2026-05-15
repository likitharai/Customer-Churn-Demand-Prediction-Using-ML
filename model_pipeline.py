from __future__ import annotations

import pathlib
from typing import List

import joblib
import numpy as np
import pandas as pd
from lightgbm import LGBMClassifier
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

ROOT = pathlib.Path(__file__).resolve().parent
DATA_PATH = ROOT / "Data" / "cleaned_telco.csv"
MODEL_PATH = ROOT / "model_pipeline.pkl"

NUMERIC_FEATURES = ["tenure", "MonthlyCharges", "TotalCharges"]
CATEGORICAL_FEATURES = [
    "gender",
    "SeniorCitizen",
    "Partner",
    "Dependents",
    "PhoneService",
    "MultipleLines",
    "InternetService",
    "OnlineSecurity",
    "OnlineBackup",
    "DeviceProtection",
    "TechSupport",
    "StreamingTV",
    "StreamingMovies",
    "Contract",
    "PaperlessBilling",
    "PaymentMethod",
]
TARGET_COLUMN = "Churn_flag"


def load_data(data_path: pathlib.Path | str = DATA_PATH) -> pd.DataFrame:
    df = pd.read_csv(data_path)
    drop_columns = [c for c in ["Unnamed: 0", "customerID"] if c in df.columns]
    if drop_columns:
        df = df.drop(columns=drop_columns)

    if "TotalCharges" in df.columns:
        df["TotalCharges"] = pd.to_numeric(df["TotalCharges"], errors="coerce").fillna(0.0)

    if TARGET_COLUMN in df.columns:
        df[TARGET_COLUMN] = pd.to_numeric(df[TARGET_COLUMN], errors="coerce")
        df = df.dropna(subset=[TARGET_COLUMN])
        df[TARGET_COLUMN] = df[TARGET_COLUMN].astype(int)
    elif "Churn" in df.columns:
        df[TARGET_COLUMN] = df["Churn"].map({"Yes": 1, "No": 0}).astype(int)

    return df


def build_pipeline() -> Pipeline:
    numeric_transformer = Pipeline(
        [
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )
    categorical_transformer = Pipeline(
        [
            ("imputer", SimpleImputer(strategy="most_frequent", fill_value="Missing")),
            (
                "onehot",
                OneHotEncoder(handle_unknown="ignore", sparse_output=False),
            ),
        ]
    )

    preprocessor = ColumnTransformer(
        [
            ("num", numeric_transformer, NUMERIC_FEATURES),
            ("cat", categorical_transformer, CATEGORICAL_FEATURES),
        ],
        remainder="drop",
    )

    classifier = LGBMClassifier(
        random_state=42,
        n_estimators=600,
        learning_rate=0.045,
        num_leaves=48,
        max_depth=7,
        subsample=0.85,
        colsample_bytree=0.75,
        class_weight="balanced",
        verbosity=-1,
    )

    pipeline = Pipeline(
        [
            ("preprocessor", preprocessor),
            ("classifier", classifier),
        ]
    )

    return pipeline


def save_model(pipeline: Pipeline, path: pathlib.Path = MODEL_PATH) -> None:
    joblib.dump(pipeline, path)


def load_model(path: pathlib.Path | str = MODEL_PATH) -> Pipeline:
    return joblib.load(path)


def get_feature_names(pipeline: Pipeline) -> List[str]:
    if "preprocessor" not in pipeline.named_steps:
        raise ValueError("Pipeline does not contain a preprocessor step.")

    transformer: ColumnTransformer = pipeline.named_steps["preprocessor"]
    numeric_names = NUMERIC_FEATURES
    cat_transformer = transformer.named_transformers_["cat"].named_steps["onehot"]
    categorical_names = cat_transformer.get_feature_names_out(CATEGORICAL_FEATURES).tolist()
    return numeric_names + categorical_names


def get_top_features(pipeline: Pipeline, top_n: int = 10) -> List[tuple[str, float]]:
    feature_names = get_feature_names(pipeline)
    classifier = pipeline.named_steps["classifier"]
    importances = getattr(classifier, "feature_importances_", None)
    if importances is None:
        raise ValueError("Classifier does not expose feature_importances_.")

    pairs = sorted(zip(feature_names, importances), key=lambda p: p[1], reverse=True)
    return pairs[:top_n]
