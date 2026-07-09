"""
Project      : Decision Intelligence Platform
Module       : evaluate.py
Author       : Likitha Rai

Description:
Evaluate the trained model using multiple performance metrics
and generate evaluation reports.
"""

import json
import warnings

import joblib
import matplotlib.pyplot as plt
import pandas as pd

from sklearn.calibration import calibration_curve

from sklearn.metrics import (

    accuracy_score,

    classification_report,

    confusion_matrix,

    ConfusionMatrixDisplay,

    precision_score,

    recall_score,

    f1_score,

    roc_auc_score,

    roc_curve,

    precision_recall_curve,

    auc,

    log_loss,

    matthews_corrcoef,

    cohen_kappa_score,

)

from src.config import (

    MODELS_DIR,

    PROCESSED_DATA_DIR,

    REPORTS_DIR,

)

from src.logger import logger

warnings.filterwarnings("ignore")


class ModelEvaluator:

    def __init__(self):

        self.model = joblib.load(

            MODELS_DIR /

            "best_model.pkl"

        )

        REPORTS_DIR.mkdir(

            parents=True,

            exist_ok=True,

        )

    # =====================================================
    # Load Test Dataset
    # =====================================================

    def load_data(self):

        logger.info(

            "Loading Test Dataset..."

        )

        X_test = pd.read_csv(

            PROCESSED_DATA_DIR /

            "x_test.csv"

        )

        y_test = pd.read_csv(

            PROCESSED_DATA_DIR /

            "y_test.csv"

        ).values.ravel()

        logger.info(

            f"Test Shape : {X_test.shape}"

        )

        return (

            X_test,

            y_test,

        )

    # =====================================================
    # Predict
    # =====================================================

    def predict(self):

        X_test, y_test = self.load_data()

        y_pred = self.model.predict(

            X_test

        )

        y_prob = self.model.predict_proba(

            X_test

        )[:, 1]

        return (

            X_test,

            y_test,

            y_pred,

            y_prob,

        )

    # =====================================================
    # Calculate Metrics
    # =====================================================

    def evaluate(self):

        (

            X_test,

            y_test,

            y_pred,

            y_prob,

        ) = self.predict()

        metrics = {

            "Accuracy":

                accuracy_score(

                    y_test,

                    y_pred,

                ),

            "Precision":

                precision_score(

                    y_test,

                    y_pred,

                ),

            "Recall":

                recall_score(

                    y_test,

                    y_pred,

                ),

            "F1 Score":

                f1_score(

                    y_test,

                    y_pred,

                ),

            "ROC AUC":

                roc_auc_score(

                    y_test,

                    y_prob,

                ),

            "Log Loss":

                log_loss(

                    y_test,

                    y_prob,

                ),

            "Matthews Correlation":

                matthews_corrcoef(

                    y_test,

                    y_pred,

                ),

            "Cohen Kappa":

                cohen_kappa_score(

                    y_test,

                    y_pred,

                ),

        }

        self.metrics = metrics

        self.classification_report = classification_report(

            y_test,

            y_pred,

            output_dict=True,

        )

        self.confusion_matrix = confusion_matrix(

            y_test,

            y_pred,

        )

        self.y_test = y_test

        self.y_pred = y_pred

        self.y_prob = y_prob

        self.X_test = X_test

        return metrics
    
    # =====================================================
    # Confusion Matrix
    # =====================================================

    def plot_confusion_matrix(self):

        fig, ax = plt.subplots(figsize=(6, 6))

        ConfusionMatrixDisplay(

            confusion_matrix=self.confusion_matrix,

        ).plot(

            cmap="Blues",

            ax=ax,

            colorbar=False,

        )

        plt.title("Confusion Matrix")

        plt.tight_layout()

        plt.savefig(

            REPORTS_DIR /

            "confusion_matrix.png",

            dpi=300,

        )

        plt.close()

        pd.DataFrame(

            self.confusion_matrix

        ).to_csv(

            REPORTS_DIR /

            "confusion_matrix.csv",

            index=False,

        )

    # =====================================================
    # ROC Curve
    # =====================================================

    def plot_roc_curve(self):

        fpr, tpr, _ = roc_curve(

            self.y_test,

            self.y_prob,

        )

        roc_score = auc(

            fpr,

            tpr,

        )

        plt.figure(figsize=(8,6))

        plt.plot(

            fpr,

            tpr,

            linewidth=2,

            label=f"AUC = {roc_score:.4f}",

        )

        plt.plot(

            [0,1],

            [0,1],

            linestyle="--",

        )

        plt.xlabel("False Positive Rate")

        plt.ylabel("True Positive Rate")

        plt.title("ROC Curve")

        plt.legend()

        plt.grid(True)

        plt.tight_layout()

        plt.savefig(

            REPORTS_DIR /

            "roc_curve.png",

            dpi=300,

        )

        plt.close()

    # =====================================================
    # Precision Recall Curve
    # =====================================================

    def plot_precision_recall_curve(self):

        precision, recall, _ = precision_recall_curve(

            self.y_test,

            self.y_prob,

        )

        plt.figure(figsize=(8,6))

        plt.plot(

            recall,

            precision,

            linewidth=2,

        )

        plt.xlabel("Recall")

        plt.ylabel("Precision")

        plt.title("Precision Recall Curve")

        plt.grid(True)

        plt.tight_layout()

        plt.savefig(

            REPORTS_DIR /

            "precision_recall_curve.png",

            dpi=300,

        )

        plt.close()

    # =====================================================
    # Calibration Curve
    # =====================================================

    def plot_calibration_curve(self):

        prob_true, prob_pred = calibration_curve(

            self.y_test,

            self.y_prob,

            n_bins=10,

        )

        plt.figure(figsize=(8,6))

        plt.plot(

            prob_pred,

            prob_true,

            marker="o",

        )

        plt.plot(

            [0,1],

            [0,1],

            linestyle="--",

        )

        plt.xlabel("Predicted Probability")

        plt.ylabel("Observed Probability")

        plt.title("Calibration Curve")

        plt.grid(True)

        plt.tight_layout()

        plt.savefig(

            REPORTS_DIR /

            "calibration_curve.png",

            dpi=300,

        )

        plt.close()

    # =====================================================
    # Probability Distribution
    # =====================================================

    def plot_probability_distribution(self):

        plt.figure(figsize=(8,6))

        plt.hist(

            self.y_prob,

            bins=25,

        )

        plt.xlabel("Predicted Probability")

        plt.ylabel("Customers")

        plt.title("Probability Distribution")

        plt.tight_layout()

        plt.savefig(

            REPORTS_DIR /

            "probability_distribution.png",

            dpi=300,

        )

        plt.close()

    # =====================================================
    # Feature Importance
    # =====================================================

    def plot_feature_importance(self):

        if not hasattr(

            self.model,

            "feature_importances_",

        ):

            return

        importance = pd.DataFrame({

            "Feature": self.X_test.columns,

            "Importance": self.model.feature_importances_,

        })

        importance = importance.sort_values(

            by="Importance",

            ascending=False,

        )

        importance.to_csv(

            REPORTS_DIR /

            "feature_importance.csv",

            index=False,

        )

        plt.figure(figsize=(10,8))

        plt.barh(

            importance["Feature"][:20][::-1],

            importance["Importance"][:20][::-1],

        )

        plt.title("Top 20 Feature Importance")

        plt.tight_layout()

        plt.savefig(

            REPORTS_DIR /

            "feature_importance.png",

            dpi=300,

        )

        plt.close()

    # =====================================================
    # Save Reports
    # =====================================================

    def save_reports(self):

        pd.DataFrame(

            self.classification_report

        ).transpose().to_csv(

            REPORTS_DIR /

            "classification_report.csv"

        )

        with open(

            REPORTS_DIR /

            "evaluation_metrics.json",

            "w",

        ) as file:

            json.dump(

                self.metrics,

                file,

                indent=4,

            )

        logger.info(

            "Evaluation Reports Saved."

        )
    # =====================================================
    # Lift Chart
    # =====================================================

    def plot_lift_chart(self):

        df = pd.DataFrame({

            "Actual": self.y_test,

            "Probability": self.y_prob,

        })

        df = df.sort_values(

            by="Probability",

            ascending=False,

        ).reset_index(drop=True)

        df["Decile"] = pd.qcut(

            df.index,

            10,

            labels=False,

        )

        lift = df.groupby(

            "Decile"

        )["Actual"].mean()

        plt.figure(figsize=(8,6))

        plt.plot(

            range(1,11),

            lift,

            marker="o",

            linewidth=2,

        )

        plt.title("Lift Chart")

        plt.xlabel("Decile")

        plt.ylabel("Average Churn")

        plt.grid(True)

        plt.tight_layout()

        plt.savefig(

            REPORTS_DIR /

            "lift_chart.png",

            dpi=300,

        )

        plt.close()

    # =====================================================
    # Gains Chart
    # =====================================================

    def plot_gains_chart(self):

        df = pd.DataFrame({

            "Actual": self.y_test,

            "Probability": self.y_prob,

        })

        df = df.sort_values(

            by="Probability",

            ascending=False,

        )

        gains = (

            df["Actual"]

            .cumsum()

            /

            df["Actual"].sum()

        )

        plt.figure(figsize=(8,6))

        plt.plot(

            gains.values,

            linewidth=2,

        )

        plt.title("Gains Chart")

        plt.xlabel("Customers")

        plt.ylabel("Cumulative Gain")

        plt.grid(True)

        plt.tight_layout()

        plt.savefig(

            REPORTS_DIR /

            "gains_chart.png",

            dpi=300,

        )

        plt.close()

    # =====================================================
    # Generate All Visualizations
    # =====================================================

    def generate_visualizations(self):

        logger.info(

            "Generating Evaluation Plots..."

        )

        self.plot_confusion_matrix()

        self.plot_roc_curve()

        self.plot_precision_recall_curve()

        self.plot_calibration_curve()

        self.plot_probability_distribution()

        self.plot_feature_importance()

        self.plot_lift_chart()

        self.plot_gains_chart()

    # =====================================================
    # Display Summary
    # =====================================================

    def display_summary(self):

        print("\n")

        print("=" * 80)

        print("MODEL EVALUATION SUMMARY")

        print("=" * 80)

        for key, value in self.metrics.items():

            print(

                f"{key:30} : {value:.4f}"

            )

        print("=" * 80)

    # =====================================================
    # Run
    # =====================================================

    def run(self):

        self.evaluate()

        self.generate_visualizations()

        self.save_reports()

        self.display_summary()

        logger.info(

            "=" * 80

        )

        logger.info(

            "MODEL EVALUATION COMPLETED"

        )

        logger.info(

            "=" * 80

        )

        print("\n")

        print("=" * 80)

        print("MODEL EVALUATION COMPLETED")

        print("=" * 80)

        print()

        print("Generated Files")

        print("-----------------------------")

        print("✔ confusion_matrix.png")

        print("✔ roc_curve.png")

        print("✔ precision_recall_curve.png")

        print("✔ calibration_curve.png")

        print("✔ probability_distribution.png")

        print("✔ lift_chart.png")

        print("✔ gains_chart.png")

        print("✔ feature_importance.png")

        print("✔ classification_report.csv")

        print("✔ evaluation_metrics.json")

        print("✔ confusion_matrix.csv")


# =====================================================
# Main
# =====================================================

if __name__ == "__main__":

    evaluator = ModelEvaluator()

    evaluator.run()            