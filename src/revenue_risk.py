"""
Project      : Decision Intelligence Platform
Module       : revenue_risk.py
Author       : Likitha Rai

Description:
Estimate revenue risk using the trained churn model.
"""

import json
import joblib
import warnings

import matplotlib.pyplot as plt
import pandas as pd

from src.config import (
    MODELS_DIR,
    PROCESSED_DATA_DIR,
    REPORTS_DIR,
)

from src.logger import logger

warnings.filterwarnings("ignore")


class RevenueRiskAnalyzer:

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
    # Load Dataset
    # =====================================================

    def load_dataset(self):

        logger.info(

            "Loading customer dataset..."

        )

        business_df= pd.read_csv(

            PROCESSED_DATA_DIR /

            "cleaned_telco.csv"

        )

        y = pd.read_csv(

            PROCESSED_DATA_DIR /

            "y_test.csv"

        ).values.ravel()

        return business_df, y

    # =====================================================
    # Predict Churn
    # =====================================================

    def predict(self):

        X, y = self.load_dataset()

        probability = self.model.predict_proba(

            X

        )[:,1]

        prediction = self.model.predict(

            X

        )

        df = X.copy()

        df["Actual_Churn"] = y

        df["Prediction"] = prediction

        df["Churn_Probability"] = probability

        self.data = df

        return df

    # =====================================================
    # Estimate Customer Lifetime Value
    # =====================================================

    @staticmethod
    def estimate_clv(

        monthly_charge,

        tenure,

    ):

        return (

            monthly_charge *

            tenure

        )

    # =====================================================
    # Revenue Risk
    # =====================================================

    def calculate_revenue_risk(self):

        df = self.predict()

        if "MonthlyCharges" not in df.columns:

            raise ValueError(

                "MonthlyCharges column missing."

            )

        if "tenure" not in df.columns:

            raise ValueError(

                "tenure column missing."

            )

        df["Estimated_CLV"] = df.apply(

            lambda row:

            self.estimate_clv(

                row["MonthlyCharges"],

                row["tenure"],

            ),

            axis=1,

        )

        df["Revenue_Risk"] = (

            df["Estimated_CLV"] *

            df["Churn_Probability"]

        )

        self.data = df

        logger.info(

            "Revenue Risk Calculated."

        )

        return df
    

    # =====================================================
    # Customer Segmentation
    # =====================================================

    def customer_segmentation(self):

        df = self.data.copy()

        conditions = [

            (df["Churn_Probability"] >= 0.80),

            (df["Churn_Probability"] >= 0.60),

            (df["Churn_Probability"] >= 0.40),

            (df["Churn_Probability"] >= 0.20),

        ]

        labels = [

            "Critical",

            "High",

            "Medium",

            "Low",

        ]

        df["Risk_Level"] = "Very Low"

        for condition, label in zip(conditions, labels):

            df.loc[condition, "Risk_Level"] = label

        self.data = df

        logger.info(

            "Customer Segmentation Completed."

        )

        return df

    # =====================================================
    # High Risk Customers
    # =====================================================

    def high_risk_customers(

        self,

        threshold=0.80,

    ):

        df = self.data.copy()

        high_risk = df[

            df["Churn_Probability"] >= threshold

        ].sort_values(

            by="Revenue_Risk",

            ascending=False,

        )

        high_risk.to_csv(

            REPORTS_DIR /

            "high_risk_customers.csv",

            index=False,

        )

        logger.info(

            "High Risk Customers Saved."

        )

        return high_risk

    # =====================================================
    # Revenue Summary
    # =====================================================

    def revenue_summary(self):

        df = self.data.copy()

        summary = {

            "Total_Customers":

                len(df),

            "Predicted_Churn":

                int(

                    df["Prediction"].sum()

                ),

            "Total_Revenue_Risk":

                round(

                    df["Revenue_Risk"].sum(),

                    2,

                ),

            "Average_CLV":

                round(

                    df["Estimated_CLV"].mean(),

                    2,

                ),

            "Average_Churn_Probability":

                round(

                    df["Churn_Probability"].mean(),

                    4,

                ),

        }

        pd.DataFrame(

            [summary]

        ).to_csv(

            REPORTS_DIR /

            "revenue_risk_summary.csv",

            index=False,

        )

        logger.info(

            "Revenue Summary Saved."

        )

        self.summary = summary

        return summary

    # =====================================================
    # Revenue by Risk Level
    # =====================================================

    def revenue_by_segment(self):

        df = self.data.copy()

        report = (

            df.groupby(

                "Risk_Level"

            )

            .agg(

                Customers=(

                    "Risk_Level",

                    "count",

                ),

                Revenue_Risk=(

                    "Revenue_Risk",

                    "sum",

                ),

                Avg_CLV=(

                    "Estimated_CLV",

                    "mean",

                ),

            )

            .reset_index()

        )

        report.to_csv(

            REPORTS_DIR /

            "revenue_risk_by_segment.csv",

            index=False,

        )

        logger.info(

            "Revenue by Segment Saved."

        )

        return report

    # =====================================================
    # Executive KPIs
    # =====================================================

    def executive_kpis(self):

        df = self.data.copy()

        kpis = {

            "Total Customers":

                len(df),

            "High Risk Customers":

                int(

                    (df["Risk_Level"] == "Critical").sum()

                ),

            "Predicted Churn":

                int(

                    df["Prediction"].sum()

                ),

            "Revenue At Risk":

                round(

                    df["Revenue_Risk"].sum(),

                    2,

                ),

            "Average CLV":

                round(

                    df["Estimated_CLV"].mean(),

                    2,

                ),

        }

        with open(

            REPORTS_DIR /

            "executive_kpis.json",

            "w",

        ) as file:

            json.dump(

                kpis,

                file,

                indent=4,

            )

        logger.info(

            "Executive KPIs Saved."

        )

        return kpis

    # =====================================================
    # Revenue Risk Visualization
    # =====================================================

    def plot_revenue_risk(self):

        df = self.data.copy()

        revenue = (

            df.groupby(

                "Risk_Level"

            )["Revenue_Risk"]

            .sum()

            .sort_values(

                ascending=False

            )

        )

        plt.figure(figsize=(8,6))

        revenue.plot(

            kind="bar"

        )

        plt.title("Revenue Risk by Customer Segment")

        plt.xlabel("Risk Level")

        plt.ylabel("Revenue at Risk")

        plt.tight_layout()

        plt.savefig(

            REPORTS_DIR /

            "revenue_risk_chart.png",

            dpi=300,

        )

        plt.close()

        logger.info(

            "Revenue Risk Chart Saved."

        )

    # =====================================================
    # Monthly Revenue Loss Estimation
    # =====================================================

    def monthly_revenue_loss(self):

        df = self.data.copy()

        report = (

            df.groupby(

                "Risk_Level"

            )

            .agg(

                Monthly_Revenue_Loss=(

                    "Revenue_Risk",

                    "sum",

                )

            )

            .reset_index()

        )

        report.to_csv(

            REPORTS_DIR /

            "monthly_revenue_loss.csv",

            index=False,

        )

        logger.info(

            "Monthly Revenue Loss Report Saved."

        )

        return report

    # =====================================================
    # Dashboard Summary
    # =====================================================

    def dashboard_summary(self):

        print("\n")

        print("=" * 80)

        print("EXECUTIVE REVENUE SUMMARY")

        print("=" * 80)

        print(

            f"Customers              : {self.summary['Total_Customers']}"

        )

        print(

            f"Predicted Churn        : {self.summary['Predicted_Churn']}"

        )

        print(

            f"Average CLV            : {self.summary['Average_CLV']:.2f}"

        )

        print(

            f"Average Churn Prob.    : {self.summary['Average_Churn_Probability']:.4f}"

        )

        print(

            f"Revenue At Risk        : ₹{self.summary['Total_Revenue_Risk']:.2f}"

        )

        print("=" * 80)

    # =====================================================
    # Run Complete Pipeline
    # =====================================================

    def run(self):

        logger.info(

            "=" * 80

        )

        logger.info(

            "Revenue Risk Analysis Started"

        )

        logger.info(

            "=" * 80

        )

        self.calculate_revenue_risk()

        self.customer_segmentation()

        self.high_risk_customers()

        self.revenue_summary()

        self.revenue_by_segment()

        self.executive_kpis()

        self.monthly_revenue_loss()

        self.plot_revenue_risk()

        self.dashboard_summary()

        logger.info(

            "=" * 80

        )

        logger.info(

            "Revenue Risk Analysis Completed"

        )

        logger.info(

            "=" * 80

        )

        print("\n")

        print("=" * 80)

        print("REVENUE RISK ANALYSIS COMPLETED")

        print("=" * 80)

        print()

        print("Generated Files")

        print("------------------------------")

        print("✔ revenue_risk_summary.csv")

        print("✔ revenue_risk_by_segment.csv")

        print("✔ monthly_revenue_loss.csv")

        print("✔ executive_kpis.json")

        print("✔ high_risk_customers.csv")

        print("✔ revenue_risk_chart.png")


# =====================================================
# Main
# =====================================================

if __name__ == "__main__":

    analyzer = RevenueRiskAnalyzer()

    analyzer.run()        