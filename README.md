# Customer-Churn-Demand-Prediction-Using-ML
This project predicts whether a customer will churn (leave the service) using telecom customer data. The prediction can help telecom companies take proactive retention actions.
---
## 🎯 Objective
To analyze customer behavior and build machine learning models that can accurately predict churn using customer demographics, service types, and account information.
---
## 🗂️ Project Structure
 Customer-Churn-Demand-Prediction/
├── README.md
├── data/
│ └── dataset.csv
├── notebooks/
│ ├── eda.ipynb # Exploratory Data Analysis
│ ├── preprocessing.ipynb # Data cleaning & preparation
│ └── modling.ipynb # Model training & evaluation
├── requirements.txt


## 🧾 Dataset Summary

The dataset contains information on telecom customers:

- **Customer Info:** gender, senior citizen, partner, dependents
- **Services Used:** internet, phone, streaming, etc.
- **Account Info:** contract type, payment method, monthly/total charges
- **Target Variable:** `Churn` (Yes/No)

---

## 🔎 1. Exploratory Data Analysis (`eda.ipynb`)

- Checked data structure, types, and duplicates
- Analyzed missing values and distributions
- Investigated churn imbalance
- Identified patterns:
  -  People with **shorter tenure** (newer customers) are more likely to churn.
  - Customers with **month-to-month contracts** leave more often.
  - **Senior citizens** tend to churn more than younger customers.
  - Having **no tech support** or **online security** is linked to higher churn.
  - Using **fiber optic internet** also seems to increase churn.

---

## 🧼 2. Data Preprocessing (`preprocessing.ipynb`)

- **Handled missing values** in `TotalCharges` (converted & filled),`Churn` etc
- **Converted data types** appropriately
- **Encoded categorical variables**:
  - Binary: Label Encoding (`Yes/No`)
  - Multi-class: One-hot encoding (e.g., `Contract`, `PaymentMethod`)
- **Scaled numeric features** like `MonthlyCharges`,`TotalCharges` and `tenure`
- **Split dataset** into train/test (typically 80/20)
- **Handled class imbalance** using SMOTE and SMOTEENN for balanced modeling

---

## 🤖 3. Model Building (`modling.ipynb`)

- Models used:
  - Logistic Regression
  - Random Forest
  - XGBoost
  - LightGBM
  - SVC
  - KNeighborsClassifier
  - AdaBoostClassifier
  - DecisionTreeClassifier
  - GaussianNB
  - GradientBoostingClassifier
- Evaluation metrics:
  - Accuracy
  - Confusion Matrix
  - Classification Report (Precision, Recall, F1)
- **Tuning:** GridSearchCV and RandomizedSearchCV were used for hyperparameter tuning.

---

## ✅ Results Summary
Sure! Here's a concise 5-line summary for your final README:

---

### 📈 Results Summary

We trained multiple ML models to predict customer churn, with **KNeighborsClassifier** achieving the highest accuracy of **98.08%** after applying **SMOTEENN** to handle class imbalance.
Evaluation using **accuracy, precision, recall, F1-score**, and the **confusion matrix** showed strong overall performance with minimal false negatives.
The classification report confirmed the model’s reliability across both churn and non-churn classes.
Other strong models included SVM, XGBoost, and Gradient Boosting, all above 96% accuracy.
These results indicate a highly effective model for churn prediction with potential for deployment.
---

## 📈 Visual Results

- Confusion matrices
- Bar plot comparing model accuracies
- Feature importance 

---

## 📌 Conclusion

- Churn is influenced by tenure, contract type, and senior citizen status.
- Handling imbalance and tuning hyperparameters improves accuracy.
- Project successfully predicts churn with over **98% accuracy**.

---

## 🚀 Future Improvements

- Try ensemble techniques like **VotingClassifier** (not yet used)
- Add a dashboard using **Streamlit** or **Gradio**
- Model deployment via Flask or Docker

---

## 🚀 App and Deployment

A new Streamlit UI app is included in `app.py`, and the model training pipeline is available in `train_model.py`.

- Install app dependencies:
  - `pip install -r requirements-app.txt`
- Train the model:
  - `python train_model.py`
- Run the UI app:
  - `streamlit run app.py`

The app uses `Data/cleaned_telco.csv` and displays churn probability, risk status, and the top model drivers.

---

## ⚙️ Requirements

Install required packages:

```bash
pip install -r requirements.txt
