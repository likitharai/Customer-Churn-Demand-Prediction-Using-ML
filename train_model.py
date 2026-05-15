from __future__ import annotations

import pathlib
from typing import Any

from model_pipeline import DATA_PATH, TARGET_COLUMN, build_pipeline, load_data, save_model
from sklearn.metrics import (accuracy_score, classification_report, confusion_matrix,
                             roc_auc_score)
from sklearn.model_selection import train_test_split


def main(data_path: pathlib.Path | str = DATA_PATH) -> None:
    df = load_data(data_path)
    feature_columns = [
        col for col in df.columns if col not in [TARGET_COLUMN, "Churn"]
    ]
    X = df[feature_columns]
    y = df[TARGET_COLUMN]

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        stratify=y,
        random_state=42,
    )

    pipeline = build_pipeline()
    pipeline.fit(X_train, y_train)
    save_model(pipeline)

    y_pred = pipeline.predict(X_test)
    y_prob = pipeline.predict_proba(X_test)[:, 1]

    print("Model saved to model_pipeline.pkl")
    print("--- Evaluation on holdout test set ---")
    print(f"Accuracy: {accuracy_score(y_test, y_pred):.4f}")
    print(f"ROC AUC: {roc_auc_score(y_test, y_prob):.4f}")
    print("Confusion Matrix:")
    print(confusion_matrix(y_test, y_pred))
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred, digits=4))


if __name__ == "__main__":
    main()
