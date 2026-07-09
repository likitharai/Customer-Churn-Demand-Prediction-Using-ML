"""
Project      : Decision Intelligence Platform
Module       : train_model.py
Author       : Likitha Rai

Description:
Train multiple ML models and automatically select the best model.
"""

import json
import warnings
from pathlib import Path

import joblib
import pandas as pd


from catboost import CatBoostClassifier
from lightgbm import LGBMClassifier
from xgboost import XGBClassifier

from sklearn.ensemble import (
    AdaBoostClassifier,
    GradientBoostingClassifier,
    RandomForestClassifier,
)

from sklearn.linear_model import LogisticRegression

from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)

from sklearn.model_selection import (
    StratifiedKFold,
    cross_val_score,
)

from sklearn.neighbors import KNeighborsClassifier

from sklearn.svm import SVC

from sklearn.tree import DecisionTreeClassifier

from src.config import (
    MODELS_DIR,
    PROCESSED_DATA_DIR,
)

from src.constants import RANDOM_STATE

from src.logger import logger


warnings.filterwarnings("ignore")


class ModelTrainer:

    def __init__(self):

        self.models = {

            "Logistic Regression":

                LogisticRegression(

                    max_iter=1000,

                    random_state=RANDOM_STATE,

                ),

            "Decision Tree":

                DecisionTreeClassifier(

                    random_state=RANDOM_STATE,

                ),

            "Random Forest":

                RandomForestClassifier(

                    n_estimators=300,

                    random_state=RANDOM_STATE,

                ),

            "Gradient Boosting":

                GradientBoostingClassifier(

                    random_state=RANDOM_STATE,

                ),

            "AdaBoost":

                AdaBoostClassifier(

                    random_state=RANDOM_STATE,

                ),

            "KNN":

                KNeighborsClassifier(

                    n_neighbors=7,

                ),

            "SVM":

                SVC(

                    probability=True,

                    random_state=RANDOM_STATE,

                ),

            "LightGBM":

                LGBMClassifier(

                    random_state=RANDOM_STATE,

                    verbosity=-1,

                ),

            "XGBoost":

                XGBClassifier(

                    random_state=RANDOM_STATE,

                    eval_metric="logloss",

                ),

            "CatBoost":

                CatBoostClassifier(

                    random_state=RANDOM_STATE,

                    verbose=False,

                ),

        }

        self.best_model = None

        self.best_model_name = None

        self.best_accuracy = 0

        self.best_roc_auc = 0.0

        self.results = []

    # ======================================================
    # Load Dataset
    # ======================================================

    def load_data(self):

        logger.info("Loading processed dataset...")

        X_train = pd.read_csv(

            PROCESSED_DATA_DIR /

            "x_train.csv"

        )

        X_test = pd.read_csv(

            PROCESSED_DATA_DIR /

            "x_test.csv"

        )

        y_train = pd.read_csv(

            PROCESSED_DATA_DIR /

            "y_train.csv"

        ).values.ravel()

        y_test = pd.read_csv(

            PROCESSED_DATA_DIR /

            "y_test.csv"

        ).values.ravel()

        logger.info(

            "Dataset Loaded Successfully."

        )

        return (

            X_train,

            X_test,

            y_train,

            y_test,

        )

    # ======================================================
    # Cross Validation
    # ======================================================

    def cross_validation(

        self,

        model,

        X,

        y,

    ):

        cv = StratifiedKFold(

            n_splits=5,

            shuffle=True,

            random_state=RANDOM_STATE,

        )

        score = cross_val_score(

            model,

            X,

            y,

            cv=cv,

            scoring="accuracy",

        )

        return score.mean()

    # ======================================================
    # Evaluate Model
    # ======================================================

    def evaluate(

        self,

        model,

        X_test,

        y_test,

    ):

        prediction = model.predict(

            X_test

        )

        probability = model.predict_proba(

            X_test

        )[:, 1]

        metrics = {

            "Accuracy":

                accuracy_score(

                    y_test,

                    prediction,

                ),

            "Precision":

                precision_score(

                    y_test,

                    prediction,

                ),

            "Recall":

                recall_score(

                    y_test,

                    prediction,

                ),

            "F1":

                f1_score(

                    y_test,

                    prediction,

                ),

            "ROC_AUC":

                roc_auc_score(

                    y_test,

                    probability,

                ),

            "Confusion_Matrix":

                confusion_matrix(

                    y_test,

                    prediction,

                ),

            "Classification_Report":

                classification_report(

                    y_test,

                    prediction,

                    output_dict=True,

                ),

        }

        return metrics
    

    # ======================================================
    # Train All Models
    # ======================================================

    def train_models(self):

        (
            X_train,
            X_test,
            y_train,
            y_test,
        ) = self.load_data()

        logger.info("=" * 70)
        logger.info("Training Models...")
        logger.info("=" * 70)

        for name, model in self.models.items():

            print("\n")
            print("=" * 70)
            print(f"Training : {name}")
            print("=" * 70)

            model.fit(
                X_train,
                y_train,
            )

            metrics = self.evaluate(
                model,
                X_test,
                y_test,
            )

            cv_score = self.cross_validation(
                model,
                X_train,
                y_train,
            )

            result = {

                "Model": name,

                "Accuracy":
                    round(metrics["Accuracy"], 4),

                "Precision":
                    round(metrics["Precision"], 4),

                "Recall":
                    round(metrics["Recall"], 4),

                "F1":
                    round(metrics["F1"], 4),

                "ROC_AUC":
                    round(metrics["ROC_AUC"], 4),

                "Cross_Validation":
                    round(cv_score, 4),

            }

            self.results.append(result)

            print(
                f"Accuracy          : {metrics['Accuracy']:.4f}"
            )

            print(
                f"Precision         : {metrics['Precision']:.4f}"
            )

            print(
                f"Recall            : {metrics['Recall']:.4f}"
            )

            print(
                f"F1 Score          : {metrics['F1']:.4f}"
            )

            print(
                f"ROC AUC           : {metrics['ROC_AUC']:.4f}"
            )

            print(
                f"Cross Validation  : {cv_score:.4f}"
            )

            print("\nConfusion Matrix")

            print(
                metrics["Confusion_Matrix"]
            )

            print("\nClassification Report")

            print(
                classification_report(
                    y_test,
                    model.predict(X_test),
                    digits=4,
                )
            )

            if metrics["ROC_AUC"] > self.best_roc_auc:

                self.best_roc_auc = metrics["ROC_AUC"]

                self.best_accuracy = metrics["Accuracy"]

                self.best_model = model

                self.best_model_name = name

        logger.info("Training Completed.")

        self.results = pd.DataFrame(
            self.results
        )

        self.results = self.results.sort_values(

            by="ROC_AUC",

            ascending=False,

        )

        print("\n")
        print("=" * 70)
        print("MODEL COMPARISON")
        print("=" * 70)

        print(self.results)

        print("\n")
        print("=" * 70)
        print(f"BEST MODEL : {self.best_model_name}")
        print(f"BEST ROC-AUC : {self.best_roc_auc:.4f}")
        print(f"BEST ACCURACY : {self.best_accuracy:.4f}")
        print("=" * 70)

        return (

            self.best_model,

            self.results,

            X_train,

        )

    # ======================================================
    # Save Best Model
    # ======================================================

    def save_best_model(self):

        MODELS_DIR.mkdir(
            parents=True,
            exist_ok=True,
        )

        model_path = MODELS_DIR / "churn_model.pkl"

        joblib.dump(
            self.best_model,
            model_path,
        )

        logger.info(
            f"Best Model Saved : {model_path}"
        )

    # ======================================================
    # Save Metrics
    # ======================================================

    def save_metrics(self):

        metrics_path = (
            MODELS_DIR /
            "model_metrics.csv"
        )

        self.results.to_csv(
            metrics_path,
            index=False,
        )

        logger.info(
            f"Metrics Saved : {metrics_path}"
        )

    # ======================================================
    # Save Best Model Information
    # ======================================================

    def save_best_model_info(self):

        info = {

            "best_model": self.best_model_name,

            "accuracy": round(
                self.best_accuracy,
                4,
            ),
             
            "roc_auc": round(
                self.best_roc_auc,
                4,
            ),

        }

        info_path = (
            MODELS_DIR /
            "best_model_info.json"
        )

        with open(
            info_path,
            "w",
        ) as file:

            json.dump(
                info,
                file,
                indent=4,
            )

        logger.info(
            f"Best Model Info Saved : {info_path}"
        )

    # ======================================================
    # Save Feature Importance
    # ======================================================

    def save_feature_importance(
        self,
        X_train,
    ):

        if hasattr(
            self.best_model,
            "feature_importances_",
        ):

            importance = pd.DataFrame(

                {

                    "Feature": X_train.columns,

                    "Importance":
                        self.best_model.feature_importances_,

                }

            )

            importance = importance.sort_values(

                by="Importance",

                ascending=False,

            )

            importance_path = (

                MODELS_DIR /

                "feature_importance.csv"

            )

            importance.to_csv(

                importance_path,

                index=False,

            )

            logger.info(

                f"Feature Importance Saved : {importance_path}"

            )

            print("\n")

            print("=" * 70)

            print("TOP 15 IMPORTANT FEATURES")

            print("=" * 70)

            print(

                importance.head(15)

            )

    # ======================================================
    # Run
    # ======================================================

    def run(self):

        (

            self.best_model,

            self.results,

            X_train,

        ) = self.train_models()

        self.save_best_model()

        self.save_metrics()

        self.save_best_model_info()

        self.save_feature_importance(

            X_train

        )

        print("\n")

        print("=" * 80)

        print("MODEL TRAINING COMPLETED SUCCESSFULLY")

        print("=" * 80)

        print()

        print("Generated Files")

        print("----------------------------")

        print("✔ churn_model.pkl")

        print("✔ model_metrics.csv")

        print("✔ best_model_info.json")

        print("✔ feature_importance.csv")

        logger.info(

            "=" * 80

        )

        logger.info(

            "MODEL TRAINING COMPLETED"

        )

        logger.info(

            "=" * 80

        )


# ======================================================
# Main
# ======================================================

if __name__ == "__main__":

    trainer = ModelTrainer()

    trainer.run()        