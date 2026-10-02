from __future__ import annotations

import datetime
import json
import pathlib
from typing import Any, Dict, List, Tuple

import joblib
import numpy as np
import pandas as pd
from lightgbm import LGBMClassifier
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    classification_report,
    cohen_kappa_score,
    confusion_matrix,
    f1_score,
    log_loss,
    matthews_corrcoef,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

ROOT = pathlib.Path(__file__).resolve().parent
DATA_PROCESSED = ROOT / "Data" / "processed" / "cleaned_telco.csv"
DATA_FALLBACK = ROOT / "Data" / "cleaned_telco.csv"
DATA_PATH = DATA_PROCESSED if DATA_PROCESSED.exists() else DATA_FALLBACK
MODEL_PATH = ROOT / "model_pipeline.pkl"
REPORTS_DIR = ROOT / "reports"

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
FEATURE_NAMES = NUMERIC_FEATURES + CATEGORICAL_FEATURES


def load_data(data_path: pathlib.Path | str = DATA_PATH) -> pd.DataFrame:
    path = pathlib.Path(data_path)
    if not path.exists():
        if DATA_FALLBACK.exists():
            path = DATA_FALLBACK
        elif DATA_PROCESSED.exists():
            path = DATA_PROCESSED
        else:
            raise FileNotFoundError(f"Cleaned dataset not found at {data_path}")

    df = pd.read_csv(path)
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
        n_estimators=150,
        learning_rate=0.05,
        num_leaves=15,
        max_depth=3,
        subsample=0.8,
        colsample_bytree=0.8,
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


def get_top_features(pipeline: Pipeline, top_n: int = 20) -> List[Tuple[str, float]]:
    feature_names = get_feature_names(pipeline)
    classifier = pipeline.named_steps["classifier"]
    importances = getattr(classifier, "feature_importances_", None)
    if importances is None:
        raise ValueError("Classifier does not expose feature_importances_.")

    pairs = sorted(zip(feature_names, [float(i) for i in importances]), key=lambda p: p[1], reverse=True)
    return pairs[:top_n]


def train_and_evaluate(
    data_path: pathlib.Path | str = DATA_PATH,
    save_artifacts: bool = True,
) -> Dict[str, Any]:
    """
    Leakage-free training and evaluation workflow:
    1. Loads cleaned data.
    2. Performs stratified train/test split BEFORE any scaling, encoding, or fitting.
    3. Fits the complete preprocessing + classifier pipeline ONLY on training data.
    4. Evaluates on the held-out untouched test set.
    5. Generates authoritative metrics, confusion matrix, and model release definitions.
    """
    df = load_data(data_path)
    X = df[FEATURE_NAMES].copy()
    y = df[TARGET_COLUMN].copy()

    # Stratified Train/Test split: 80% train, 20% holdout test
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )

    # 5-fold CV evaluation strictly on training set
    pipeline = build_pipeline()
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    cv_scores = cross_val_score(pipeline, X_train, y_train, cv=cv, scoring="roc_auc")
    mean_cv_roc_auc = float(np.mean(cv_scores))
    std_cv_roc_auc = float(np.std(cv_scores))

    # Fit pipeline strictly on training data
    pipeline.fit(X_train, y_train)

    # Predict on unseen test set
    y_pred = pipeline.predict(X_test)
    y_prob = pipeline.predict_proba(X_test)[:, 1]

    # Calculate holdout metrics
    acc = float(accuracy_score(y_test, y_pred))
    prec = float(precision_score(y_test, y_pred))
    rec = float(recall_score(y_test, y_pred))
    f1 = float(f1_score(y_test, y_pred))
    roc_auc = float(roc_auc_score(y_test, y_prob))
    pr_auc = float(average_precision_score(y_test, y_prob))
    ll = float(log_loss(y_test, y_prob))
    mcc = float(matthews_corrcoef(y_test, y_pred))
    kappa = float(cohen_kappa_score(y_test, y_pred))

    metrics = {
        "Accuracy": acc,
        "Precision": prec,
        "Recall": rec,
        "F1 Score": f1,
        "ROC AUC": roc_auc,
        "PR AUC": pr_auc,
        "Log Loss": ll,
        "Matthews Correlation": mcc,
        "Cohen Kappa": kappa,
    }

    cm = confusion_matrix(y_test, y_pred)
    cr_dict = classification_report(y_test, y_pred, output_dict=True)

    if save_artifacts:
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        save_model(pipeline, MODEL_PATH)

        # Save evaluation metrics
        with open(REPORTS_DIR / "evaluation_metrics.json", "w", encoding="utf-8") as f:
            json.dump(metrics, f, indent=4)

        # Save confusion matrix CSV
        cm_df = pd.DataFrame(cm, index=[0, 1], columns=[0, 1])
        cm_df.to_csv(REPORTS_DIR / "confusion_matrix.csv", index=False)

        # Save classification report CSV
        cr_df = pd.DataFrame(cr_dict).transpose()
        cr_df.to_csv(REPORTS_DIR / "classification_report.csv")

        # Save feature importance
        top_feats = get_top_features(pipeline, top_n=len(get_feature_names(pipeline)))
        feat_df = pd.DataFrame(top_feats, columns=["Feature", "Importance"])
        feat_df.to_csv(REPORTS_DIR / "feature_importance.csv", index=False)
        with open(REPORTS_DIR / "feature_importance.json", "w", encoding="utf-8") as f:
            json.dump(dict(top_feats), f, indent=4)

        # Save authoritative Model Release specification
        model_release = {
            "model_name": "LightGBM Churn Classifier",
            "model_version": "1.0.0",
            "status": "AUTHORITATIVE_PRODUCTION",
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "random_seed": 42,
            "dataset_info": {
                "dataset_file": "Data/processed/cleaned_telco.csv",
                "total_rows": len(df),
                "total_features": len(FEATURE_NAMES),
                "target_column": TARGET_COLUMN,
                "target_positive_class_ratio": float(y.mean()),
                "train_rows": len(X_train),
                "test_rows": len(X_test),
                "test_split_ratio": 0.20,
            },
            "features": {
                "numeric_features": NUMERIC_FEATURES,
                "categorical_features": CATEGORICAL_FEATURES,
                "transformed_feature_count": len(get_feature_names(pipeline)),
            },
            "training_method": {
                "algorithm": "LightGBM Classifier",
                "pipeline": "Scikit-Learn Pipeline with ColumnTransformer (imputation + scaling + onehot) and LGBMClassifier",
                "class_imbalance_strategy": "Cost-sensitive learning (class_weight='balanced') inside training pipeline",
                "leakage_prevention": "Preprocessing transformers fitted strictly on training split; holdout test split untouched until final evaluation",
                "hyperparameters": {
                    "n_estimators": 150,
                    "learning_rate": 0.05,
                    "num_leaves": 15,
                    "max_depth": 3,
                    "subsample": 0.8,
                    "colsample_bytree": 0.8,
                    "class_weight": "balanced",
                    "random_state": 42,
                },
            },
            "validation": {
                "cross_validation": {
                    "strategy": "5-Fold Stratified K-Fold (Training data only)",
                    "mean_roc_auc": round(mean_cv_roc_auc, 4),
                    "std_roc_auc": round(std_cv_roc_auc, 4),
                },
                "holdout_evaluation": {
                    "evaluation_set": "Data/processed/x_test_raw.csv",
                    "samples": len(X_test),
                    "metrics": {k: round(v, 4) for k, v in metrics.items()},
                    "confusion_matrix": {
                        "tn": int(cm[0, 0]),
                        "fp": int(cm[0, 1]),
                        "fn": int(cm[1, 0]),
                        "tp": int(cm[1, 1]),
                    },
                },
            },
        }

        with open(REPORTS_DIR / "model_release.json", "w", encoding="utf-8") as f:
            json.dump(model_release, f, indent=4)

    return {
        "metrics": metrics,
        "cv_roc_auc": mean_cv_roc_auc,
        "confusion_matrix": cm,
    }


if __name__ == "__main__":
    print("Executing authoritative training & evaluation workflow...")
    results = train_and_evaluate(save_artifacts=True)
    print("Training and evaluation completed successfully!")
    print(f"5-Fold CV ROC-AUC: {results['cv_roc_auc']:.4f}")
    print("Holdout Test Metrics:")
    for k, v in results["metrics"].items():
        print(f"  {k}: {v:.4f}")

