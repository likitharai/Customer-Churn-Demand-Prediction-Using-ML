from __future__ import annotations

import pathlib
import sys

import pandas as pd
import streamlit as st

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1] / "Customer-Churn-Demand-Prediction-Using-ML"
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from model_pipeline import MODEL_PATH, load_model, load_data, get_top_features

DATA_PATH = PROJECT_ROOT / "Data" / "cleaned_telco.csv"


def build_input_row() -> pd.DataFrame:
    st.sidebar.header("Customer profile")
    data = {
        "gender": st.sidebar.selectbox("Gender", ["Female", "Male"]),
        "SeniorCitizen": st.sidebar.selectbox("Senior citizen", ["No", "Yes"]),
        "Partner": st.sidebar.selectbox("Partner", ["No", "Yes"]),
        "Dependents": st.sidebar.selectbox("Dependents", ["No", "Yes"]),
        "tenure": st.sidebar.slider("Tenure (months)", 0, 72, 12),
        "PhoneService": st.sidebar.selectbox("Phone service", ["No", "Yes"]),
        "MultipleLines": st.sidebar.selectbox(
            "Multiple lines", ["No", "Yes", "No phone service"]
        ),
        "InternetService": st.sidebar.selectbox(
            "Internet service", ["DSL", "Fiber optic", "No"]
        ),
        "OnlineSecurity": st.sidebar.selectbox(
            "Online security", ["No", "Yes", "No internet service"]
        ),
        "OnlineBackup": st.sidebar.selectbox(
            "Online backup", ["No", "Yes", "No internet service"]
        ),
        "DeviceProtection": st.sidebar.selectbox(
            "Device protection", ["No", "Yes", "No internet service"]
        ),
        "TechSupport": st.sidebar.selectbox(
            "Tech support", ["No", "Yes", "No internet service"]
        ),
        "StreamingTV": st.sidebar.selectbox(
            "Streaming TV", ["No", "Yes", "No internet service"]
        ),
        "StreamingMovies": st.sidebar.selectbox(
            "Streaming movies", ["No", "Yes", "No internet service"]
        ),
        "Contract": st.sidebar.selectbox(
            "Contract", ["Month-to-month", "One year", "Two year"]
        ),
        "PaperlessBilling": st.sidebar.selectbox("Paperless billing", ["No", "Yes"]),
        "PaymentMethod": st.sidebar.selectbox(
            "Payment method",
            [
                "Electronic check",
                "Mailed check",
                "Bank transfer (automatic)",
                "Credit card (automatic)",
            ],
        ),
        "MonthlyCharges": st.sidebar.number_input(
            "Monthly charges", min_value=0.0, max_value=2000.0, value=50.0, step=0.1
        ),
        "TotalCharges": st.sidebar.number_input(
            "Total charges", min_value=0.0, max_value=50000.0, value=1000.0, step=1.0
        ),
    }
    return pd.DataFrame([data])


def main() -> None:
    st.set_page_config(page_title="Telecom Churn Predictor", layout="wide")
    st.title("📊 Telecom Customer Churn Prediction")
    st.markdown(
        "Use the sidebar to create a customer profile and predict churn risk with a trained LightGBM model."
    )

    model = None
    if MODEL_PATH.exists():
        model = load_model(MODEL_PATH)
    else:
        st.warning(
            "No trained model found. Run `python train_model.py` in this folder first."
        )

    input_df = build_input_row()
    st.subheader("Current customer profile")
    st.dataframe(input_df.T, use_container_width=True)

    if st.button("Predict churn risk"):
        if model is None:
            st.error("Model not available yet. Train the model and refresh the app.")
            return

        prediction = model.predict(input_df)[0]
        probability = model.predict_proba(input_df)[0, 1]
        label = "Churn likely" if prediction == 1 else "Churn unlikely"
        st.metric("Prediction", label, delta=f"{probability:.1%} probability")

        st.markdown("### Risk details")
        st.write(
            "This model uses a LightGBM classifier with engineered preprocessing for telecom churn data."
        )

        if hasattr(model.named_steps["classifier"], "feature_importances_"):
            top_features = get_top_features(model, top_n=8)
            importance_df = pd.DataFrame(
                top_features, columns=["Feature", "Importance"]
            )
            st.write("#### Top model drivers")
            st.dataframe(importance_df, use_container_width=True)


    if st.button("Show dataset sample"):
        df = load_data(DATA_PATH)
        st.write(df.head(10))


if __name__ == "__main__":
    main()
