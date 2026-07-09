"""
Project      : Decision Intelligence Platform
Module       : predict.py
Author       : Likitha Rai

Description:
Predict customer churn using the trained model.
"""

import joblib
import pandas as pd

from src.config import MODELS_DIR
from src.logger import logger


class ChurnPredictor:

    def __init__(self):

        self.model = joblib.load(

            MODELS_DIR /

            "churn_model.pkl"

        )

        self.pipeline = joblib.load(

            MODELS_DIR /

            "preprocessing_pipeline.pkl"

        )

        self.feature_columns = joblib.load(

            MODELS_DIR /

            "feature_columns.pkl"

        )
        self.label_encoders = joblib.load(
            MODELS_DIR / "label_encoders.pkl"
        )

        self.scaler = joblib.load(
            MODELS_DIR / "standard_scaler.pkl"
        )

    # ==========================================================
    # Prepare Input
    # ==========================================================

    def prepare_input(self, customer_data):

        if isinstance(customer_data, dict):
            customer_data = pd.DataFrame([customer_data])

        # Encode categorical columns
        for column, encoder in self.label_encoders.items():

            if column in customer_data.columns:

                customer_data[column] = encoder.transform(
                    customer_data[column]
                )

        customer_data = customer_data.reindex(
            columns=self.feature_columns,
            fill_value=0,
        )

        return customer_data

    # ==========================================================
    # Predict
    # ==========================================================

    def predict(

        self,

        customer_data,

    ):

        customer_data = self.prepare_input(

            customer_data

        )

        prediction = self.model.predict(

            customer_data

        )[0]

        probability = self.model.predict_proba(

            customer_data

        )[0][1]

        risk = self.risk_level(

            probability

        )

        logger.info(

            f"Prediction : {prediction}"

        )

        return {

            "prediction": int(prediction),

            "probability": round(

                float(probability),

                4,

            ),

            "risk_level": risk,

        }

    # ==========================================================
    # Risk Level
    # ==========================================================

    @staticmethod
    def risk_level(probability):

        if probability >= 0.80:

            return "Very High"

        elif probability >= 0.60:

            return "High"

        elif probability >= 0.40:

            return "Medium"

        elif probability >= 0.20:

            return "Low"

        else:

            return "Very Low"
        

    # ==========================================================
    # Batch Prediction
    # ==========================================================

    def predict_batch(self, dataframe):

        dataframe = self.prepare_input(dataframe)

        predictions = self.model.predict(dataframe)

        probabilities = self.model.predict_proba(dataframe)[:, 1]

        result = dataframe.copy()

        result["Prediction"] = predictions

        result["Probability"] = probabilities.round(4)

        result["Risk_Level"] = result["Probability"].apply(
            self.risk_level
        )

        return result

    # ==========================================================
    # Save Prediction Results
    # ==========================================================

    def save_predictions(

        self,

        dataframe,

        filename="predictions.csv",

    ):

        output_path = MODELS_DIR.parent / "reports"

        output_path.mkdir(

            parents=True,

            exist_ok=True,

        )

        file_path = output_path / filename

        dataframe.to_csv(

            file_path,

            index=False,

        )

        logger.info(

            f"Predictions Saved : {file_path}"

        )

        return file_path

    # ==========================================================
    # High Risk Customers
    # ==========================================================

    @staticmethod
    def high_risk_customers(

        dataframe,

        threshold=0.80,

    ):

        return dataframe[

            dataframe["Probability"] >= threshold

        ].sort_values(

            by="Probability",

            ascending=False,

        )

    # ==========================================================
    # Prediction Summary
    # ==========================================================

    @staticmethod
    def prediction_summary(dataframe):

        print("\n")

        print("=" * 60)

        print("Prediction Summary")

        print("=" * 60)

        print(

            dataframe["Risk_Level"]

            .value_counts()

        )

        print()

        print(

            dataframe["Prediction"]

            .value_counts()

        )

    # ==========================================================
    # Predict CSV File
    # ==========================================================

    def predict_csv(

        self,

        csv_path,

    ):

        logger.info(

            f"Loading : {csv_path}"

        )

        df = pd.read_csv(

            csv_path

        )

        predictions = self.predict_batch(

            df

        )

        self.prediction_summary(

            predictions

        )

        self.save_predictions(

            predictions

        )

        return predictions


# ==========================================================
# Main
# ==========================================================

if __name__ == "__main__":

    predictor = ChurnPredictor()

    sample = {

        "gender": "Female",

        "SeniorCitizen": 0,

        "Partner": "Yes",

        "Dependents": "No",

        "tenure": 10,

        "PhoneService": "Yes",

        "MultipleLines": "No",

        "InternetService": "Fiber optic",

        "OnlineSecurity": "No",

        "OnlineBackup": "Yes",

        "DeviceProtection": "No",

        "TechSupport": "No",

        "StreamingTV": "Yes",

        "StreamingMovies": "Yes",

        "Contract": "Month-to-month",

        "PaperlessBilling": "Yes",

        "PaymentMethod": "Electronic check",

        "MonthlyCharges": 89.35,

        "TotalCharges": 893.50,

    }

    result = predictor.predict(sample)

    print("\n")

    print("=" * 60)

    print("Prediction Result")

    print("=" * 60)

    print(result)        