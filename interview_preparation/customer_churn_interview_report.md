# Customer Churn Prediction: Interview Preparation Report

## Evidence policy

This report is based only on files present in the repository, including source code, notebooks, CSV/JSON outputs, configuration, SQL, tests, and documentation. Where artifacts disagree, the disagreement is recorded. A value described as current is tied to the implemented pipeline or a persisted artifact, not only to README text. Information that cannot be verified is written as **Not found in project**.

The repository contains a current ML/API application and older notebook/documentation paths. They should not be presented as one perfectly consistent experiment.

## 1. Project Overview

### Project title

The repository describes the product as a **Decision Intelligence Platform** and a customer churn/revenue-risk platform named **RetainIQ** in `PRODUCT.md`. The project is a telecom customer churn prediction and retention workflow system.

### Problem statement

Predict whether a telecom customer will churn, estimate the probability and business risk, explain important drivers, estimate revenue at risk, and support retention actions through an application workflow.

### Business problem

Customer churn causes recurring revenue loss. The project turns customer demographic, service, contract, billing, and tenure data into churn-risk scores so business users can prioritize customers and record retention activity.

### Objective

The implemented ML objective is binary classification of the churn target. The wider product objective is to connect scoring to a risk queue, revenue-risk analysis, recommendations, interactions, follow-up tasks, retention outcomes, and audit records.

### Why churn prediction is useful

A probability-ranked customer list can help a retention team focus limited outreach on customers who appear more likely to leave. The project also combines probability with customer value in revenue-risk outputs. The repository does not contain a measured causal study proving that the recommendations reduce churn.

### Users and stakeholders

Verified or described users include managers, administrators, customer-success/retention agents, and business users viewing executive and revenue-risk dashboards. The product documentation defines manager, admin, and agent workflows. Exact organization or company users are **Not found in project**.

### System input and output

**Input:** A customer record or CSV containing telecom fields such as `gender`, `SeniorCitizen`, `tenure`, service selections, `Contract`, `PaymentMethod`, `MonthlyCharges`, and `TotalCharges`. The API also accepts imported workspace customers.

**ML output:** `prediction` (`0` or `1`), churn `probability`, `risk_level`, and `prediction_label` (`Churn likely` or `Churn unlikely`).

**Operational output:** Prediction records can include probability, risk level, prediction label, revenue at risk, model version, and an input snapshot. The API also supports customers, interactions, tasks, recommendations, retention outcomes, and audit events.

### End-to-end workflow

1. Load `Data/raw/telco_churn.csv`.
2. Remove duplicate rows, normalize categorical values, convert `TotalCharges`, and create a binary target.
3. Split the cleaned data with a stratified 80/20 split and `random_state=42`.
4. Fit a training-only `ColumnTransformer` with median numeric imputation, scaling, categorical imputation, and one-hot encoding.
5. Save transformed data and a SMOTE-resampled training artifact. The current `ModelTrainer` loads the non-resampled transformed training file.
6. Train and compare nine available model types when optional libraries are installed.
7. Evaluate on the untouched holdout test split and calculate five-fold stratified ROC-AUC.
8. Select the highest holdout ROC-AUC model and persist it.
9. Optionally tune the selected model with Optuna and overwrite `best_model.pkl`.
10. Load the saved model and preprocessing pipeline for single or batch prediction.
11. Expose scoring through the FastAPI service and display analysis through Streamlit and the React frontend.
12. Use model scores in revenue-risk, explanation, recommendation, and retention-workflow features.

## 2. Dataset

### Dataset source and size

The actual raw file is `Data/raw/telco_churn.csv`. It contains **5,043 rows and 22 columns**, including `Unnamed: 0`, `customerID`, 19 customer attributes, and `Churn`. The README says 7,043 customers and 21 features, but that claim does not match the raw file currently in the repository. The cleaned file contains **5,042 rows and 22 columns** after the one missing target row is removed.

The dataset source URL or named external provider is **Not found in project**. The filename and telecom field names indicate a Telco churn dataset, but no source citation is present in the inspected project files.

### Features and meanings

The project does not provide a formal data dictionary. The meanings below are directly represented by the field names and their values in the project; more detailed business definitions are **Not found in project**.

| Feature | Meaning represented in project |
|---|---|
| `Unnamed: 0` | Input/index-like column; dropped by cleaning when present. |
| `customerID` | Customer identifier; excluded from model features. |
| `gender` | Customer gender category. |
| `SeniorCitizen` | Senior-citizen indicator; stored as a categorical-looking field in the raw file. |
| `Partner` | Whether the customer has a partner. |
| `Dependents` | Whether the customer has dependents. |
| `tenure` | Number of months with the provider. |
| `PhoneService` | Whether phone service is subscribed. |
| `MultipleLines` | Multiple-line phone-service category, including no phone service in raw values. |
| `InternetService` | Internet-service category. |
| `OnlineSecurity` | Online-security service category. |
| `OnlineBackup` | Online-backup service category. |
| `DeviceProtection` | Device-protection service category. |
| `TechSupport` | Technical-support service category. |
| `StreamingTV` | Streaming-TV service category. |
| `StreamingMovies` | Streaming-movies service category. |
| `Contract` | Contract term category. |
| `PaperlessBilling` | Whether paperless billing is enabled. |
| `PaymentMethod` | Payment method category. |
| `MonthlyCharges` | Monthly charge amount. |
| `TotalCharges` | Total charge amount; raw values are read as strings and converted to numeric. |
| `Churn` | Original churn label. `Yes` and `No` are mapped to the binary target. |

### Target

The training target is `Churn_flag`, created by the data loader from `Churn`: `Yes -> 1` and `No -> 0`. The raw file also contains `True` and `False` values; the cleaner normalizes selected categorical values to `Yes`/`No` before target creation.

Cleaned target distribution: `0 / No = 3,706` and `1 / Yes = 1,336`, out of 5,042 rows. This is approximately 73.5% class 0 and 26.5% class 1. The untouched test target contains `742` zeros and `267` ones.

### Missing values

Raw missing values verified from the CSV:

- `MultipleLines`: 269
- `OnlineSecurity`: 651
- `OnlineBackup`: 651
- `DeviceProtection`: 651
- `TechSupport`: 651
- `StreamingTV`: 651
- `StreamingMovies`: 651
- `TotalCharges`: 5 pandas `NaN` values; there are also 3 blank-string values
- `Churn`: 1

The raw total is 4,181 pandas-missing values. The cleaning code converts `TotalCharges` to numeric and fills its missing values with the median, normalizes categorical values, and drops rows with missing churn labels. Later preprocessing also contains defensive imputers.

### Duplicates

The raw CSV has **0 duplicate rows**. The cleaned CSV also has **0 duplicate rows**. The transformed `x_train.csv` has 10 duplicate rows after transformation, and the SMOTE output has 14 duplicate rows; those are transformed feature rows and are not evidence of duplicate raw customers.

### Categorical and numerical features

Raw pandas dtypes show `tenure` and `MonthlyCharges` as numeric, while `TotalCharges` and most other fields are strings. The preprocessing code dynamically treats numeric/bool fields as numeric and object/category fields as categorical after the identifier and target columns are removed. `TotalCharges` is made numeric during cleaning.

### Class imbalance

The cleaned target is imbalanced toward non-churn (`3,706` vs `1,336`). The 80/20 split preserves the ratio with stratification. The preprocessing code creates a balanced training artifact with SMOTE: `5,928` rows, `2,964` per class. However, the current `ModelTrainer` reads `Data/processed/x_train.csv` and `y_train.csv`, not the resampled files, so the saved model-comparison results are not demonstrably trained on the SMOTE artifact.

### Important EDA observations

The EDA notebook records these patterns: short-tenure customers churn more; month-to-month customers churn more; senior citizens churn more; fiber-optic customers show higher churn; customers without tech support or online security show higher churn; and electronic-check users show higher churn. These are associations in the project EDA, not causal findings.

## 3. Data Preprocessing

The controlling current implementation is in `ml_pipeline/src/data_loader.py` and `ml_pipeline/src/preprocess.py`.

| Step | What was done | Why | How implemented |
|---|---|---|---|
| Load | Read the raw or cleaned CSV. | Establish a repeatable file-based pipeline. | `pandas.read_csv` with configured `Data/raw` and `Data/processed` paths. |
| Duplicate handling | Remove duplicate full rows. | Avoid repeated observations. | `df.drop_duplicates().copy()`. |
| Whitespace cleanup | Strip whitespace from object columns. | Normalize category values. | Apply `str.strip()` to object columns. |
| Boolean/category normalization | Convert selected `True`, `False`, `1`, `0`, `No internet service`, and `No phone service` values to `Yes`/`No`. | Reduce inconsistent representations in selected binary/service fields. | A replacement dictionary is applied to listed categorical columns. |
| `TotalCharges` | Convert to numeric and fill missing values with the median. | Make the billing field usable by numeric preprocessing and avoid conversion failures. | `pd.to_numeric(errors="coerce")`, followed by `fillna(median)`. |
| Target cleaning | Remove missing target rows and map churn labels to integers. | Produce a valid binary supervised-learning target. | Missing labels are dropped; lowercased `yes/no` maps to `1/0`. Invalid target values raise an error. |
| Identifier removal | Drop `Unnamed: 0` and `customerID`. | Prevent an index/customer identifier from being used as a predictive feature. | Explicit drops in the loader/preprocessor/predictor. |
| Split | Make an 80/20 train/test split, stratified by target. | Preserve class proportions in the holdout. | `train_test_split(..., test_size=TEST_SIZE, stratify=y, random_state=42)`. |
| Numeric imputation | Median imputation. | Provide a value for missing numeric inputs. | `SimpleImputer(strategy="median")` in the numeric pipeline. |
| Numeric scaling | Standardize numeric features. | Put numeric variables on a comparable scale, especially for linear/SVM models. | `StandardScaler()` after imputation. |
| Categorical imputation | Most-frequent imputation. | Handle missing/unseen categorical inputs. | `SimpleImputer(strategy="most_frequent")`. |
| Encoding | One-hot encode categories and ignore unknown categories at inference. | Convert categories to model-readable numeric columns while avoiding prediction failure for a new category. | `OneHotEncoder(handle_unknown="ignore", sparse_output=False)`. |
| Leakage prevention | Fit transformations only on training rows; keep test rows untouched for evaluation. | Prevent test information from affecting preprocessing. | `pipeline.fit_transform(X_train_raw)` and `pipeline.transform(X_test_raw)`. |
| Resampling | Create a balanced training artifact with SMOTE. | Address the class imbalance for a possible modeling workflow. | `SMOTE(random_state=42).fit_resample(X_train_processed, y_train)`. |
| Feature selection | Drop identifier and target fields; no statistical feature-selection algorithm is present. | Keep non-predictive identifiers out. | Explicit column drops only. |
| Feature engineering | A separate helper creates `tenure_group`, `charge_per_tenure`, and `service_count`. | Represent tenure bands, a charge/tenure ratio, and service count. | `engineer_features()` in `feature_engineering.py`. |
| Feature engineering usage | The helper is not called by the current `Preprocessor.process()` flow. | Important for accurate interview claims. | Current model inputs are generated by `split_xy()` and the `ColumnTransformer`; engineered fields do not appear in the persisted feature list. |

### Preprocessing artifacts

The pipeline saves `preprocessing_pipeline.pkl`, `feature_columns.pkl`, transformed train/test CSVs, and resampled CSVs. The current transformed feature files have 41 columns. The saved transformed names include numeric fields such as `numeric__tenure`, `numeric__MonthlyCharges`, and `numeric__TotalCharges`, plus one-hot categorical fields.

### Random state and validation

The central random state is `42`. Model comparison uses five-fold `StratifiedKFold` with shuffling and random state `42`; tuning uses the same five-fold ROC-AUC setup. A separate validation set is not created; the project uses the test split as a holdout and cross-validation on the training split.

### Caveats

The raw source contains mixed representations such as `True/False` and `Yes/No`, and persisted feature names show both forms in some places. The repository does not contain a formal data-contract test proving that every production input matches the training schema.

## 4. Exploratory Data Analysis

The main EDA content is in `ml_pipeline/Notebooks/EDA.ipynb`.

| Analysis/visualization | What it shows | Project finding | Why it matters |
|---|---|---|---|
| Dataset inspection and shape/dtypes | Rows, columns, types, and sample values. | Raw data contains mixed types and missing service/billing values. | Identifies cleaning and encoding requirements. |
| Missing-value inspection | Missing count by column. | Service fields and `TotalCharges` contain missing values; churn has a missing label. | Missingness must be handled before training. |
| Numeric summaries | Descriptive statistics for numeric fields. | The notebook examines tenure and charges. Exact saved summary values are **Not found in project**. | Helps identify scale and plausible distributions. |
| Churn distribution | Counts of churn labels. | Churn is the minority class. | Supports stratification and imbalance-aware evaluation. |
| Boxplots | Numeric feature distributions by churn. | The notebook examines differences in tenure and charges by churn. Exact plotted values are **Not found in project**. | Can reveal group separation and outliers. |
| Histograms | Numeric distributions. | The notebook explores tenure and charge distributions. | Shows concentration and skew relevant to modeling. |
| Categorical churn comparisons | Churn rates/counts across contract, services, demographics, billing, and payment categories. | Month-to-month, fiber optic, electronic check, senior citizens, and missing support/security services are associated with higher churn. | Provides interpretable retention segments and candidate features. |
| Correlation heatmap | Numeric correlations. | A saved numeric correlation table is **Not found in project**. | Helps detect redundancy and relationships among numeric fields. |
| Manual conclusions | Written EDA interpretation. | The notebook contains the findings listed above. | Provides business hypotheses for the churn model. |

Notebook figures are not treated as proof of causal effects. The notebook also uses older/stale paths, so its exact execution state is not fully reproducible from the current machine-independent repository.

## 5. Machine Learning Models

### Models actually implemented in the current factory

`ml_pipeline/src/model_config.py` supports nine model names:

- Logistic Regression
- Random Forest
- Decision Tree
- Gradient Boosting
- AdaBoost
- XGBoost
- LightGBM
- CatBoost
- Calibrated SVM

The comparison artifact contains all nine listed models. The factory uses optional imports for XGBoost, LightGBM, and CatBoost; if an optional dependency is absent, that model is skipped.

| Model | Selection rationale supported by code | Important configured values | Advantages | Limitations in this project |
|---|---|---|---|---|
| Logistic Regression | Baseline linear classifier. | `max_iter=2000`, `class_weight="balanced"`. | Interpretable baseline and probability output. | Linear decision boundary; lower accuracy in the saved comparison. |
| Random Forest | Nonlinear tree ensemble. | `n_estimators=400`, `class_weight="balanced_subsample"`, `n_jobs=-1`. | Captures nonlinear interactions and gives feature importance. | More complex and did not have the best ROC-AUC. |
| Decision Tree | Single nonlinear tree baseline. | `class_weight="balanced"`, `random_state=42`. | Easy to explain. | Lower saved ROC-AUC and greater overfitting risk than ensembles. |
| Gradient Boosting | Sequential tree boosting and selected by holdout ROC-AUC. | Default comparison model uses `random_state=42`; tuned artifact uses values below. | Strong ranking performance in the saved comparison. | Missed many actual churners at the default decision threshold. |
| AdaBoost | Boosting ensemble. | `n_estimators=250`, `random_state=42`. | Combines weak learners. | Lower ROC-AUC than Gradient Boosting in the comparison. |
| XGBoost | Gradient-boosted tree implementation. | `n_estimators=300`, `learning_rate=0.05`, `max_depth=4`, `subsample=0.9`, `colsample_bytree=0.9`, `tree_method="hist"`. | Strong nonlinear model and efficient histogram training. | Optional dependency and slightly lower ROC-AUC than Gradient Boosting. |
| LightGBM | Efficient gradient boosting implementation. | `n_estimators=300`, `learning_rate=0.05`, `subsample=0.9`, `colsample_bytree=0.9`, `verbosity=-1`. | Efficient on tabular data. | Lowest boosting ROC-AUC in the current comparison. |
| CatBoost | Boosting implementation available through optional dependency. | `iterations=400`, `learning_rate=0.05`, `depth=6`, `verbose=False`. | Strong tabular learner. | Lower ROC-AUC than Gradient Boosting in the saved table. |
| SVM | SVC wrapped in `CalibratedClassifierCV` to expose probabilities. | Balanced class weights, default SVC parameters unless tuned. | Good nonlinear boundary and relatively strong recall/F1. | Probability calibration adds complexity; ROC-AUC lower than top models. |

### Training procedure

`ModelTrainer` loads `x_train.csv`, `x_test.csv`, `y_train.csv`, and `y_test.csv`, fits every available candidate on the transformed training file, evaluates the untouched test file, calculates five-fold training-set cross-validation ROC-AUC, writes `model_metrics.csv`, and selects the highest holdout ROC-AUC.

The project also contains `HyperparameterTuner`. It reads the selected model name, runs 100 Optuna TPE trials using five-fold stratified ROC-AUC, trains the selected model on the processed training data with the best parameters, and overwrites `best_model.pkl`.

## 6. Model Comparison

### Current saved comparison

Source: `ml_pipeline/models/model_metrics.csv`. Values are the persisted comparison results rounded to four decimals.

| Model | Accuracy | Precision | Recall | F1-score | ROC-AUC | 5-fold CV ROC-AUC |
|---|---:|---:|---:|---:|---:|---:|
| Gradient Boosting | 0.7998 | 0.6395 | 0.5581 | 0.5960 | 0.8553 | 0.8453 |
| XGBoost | 0.7958 | 0.6298 | 0.5543 | 0.5896 | 0.8538 | 0.8413 |
| CatBoost | 0.7998 | 0.6444 | 0.5431 | 0.5894 | 0.8537 | 0.8357 |
| AdaBoost | 0.7948 | 0.6316 | 0.5393 | 0.5818 | 0.8522 | 0.8474 |
| Logistic Regression | 0.7384 | 0.5034 | 0.8202 | 0.6239 | 0.8513 | 0.8472 |
| Random Forest | 0.8038 | 0.6605 | 0.5318 | 0.5892 | 0.8467 | 0.8323 |
| SVM | 0.7889 | 0.5993 | 0.6105 | 0.6048 | 0.8348 | 0.8327 |
| LightGBM | 0.7780 | 0.5907 | 0.5243 | 0.5556 | 0.8330 | 0.8263 |
| Decision Tree | 0.7354 | 0.5000 | 0.4831 | 0.4914 | 0.6543 | 0.6420 |

### Persisted final evaluation artifact

Source: `reports/evaluation_metrics.json`, `reports/confusion_matrix.csv`, and `reports/classification_report.csv`.

- Accuracy: `0.8017839444995044`
- Precision: `0.645021645021645`
- Recall: `0.5580524344569289`
- F1-score: `0.5983935742971888`
- ROC-AUC: `0.857715759613152`
- Log loss: `0.4024356135756316`
- Matthews correlation: `0.4698875610634476`
- Cohen kappa: `0.46772593952438235`

Confusion matrix, with rows as actual and columns as predicted:

| | Predicted 0 | Predicted 1 |
|---|---:|---:|
| Actual 0 | 660 | 82 |
| Actual 1 | 118 | 149 |

The holdout contains 742 actual non-churners and 267 actual churners. The matrix means 149 churners were detected and 118 were missed in this artifact. The churn-class precision is approximately 64.5% and recall approximately 55.8%.

### Why the final model was selected

The current comparison code selects by highest holdout ROC-AUC. In `model_metrics.csv`, Gradient Boosting has the highest comparison ROC-AUC (`0.8553`). The final evaluation JSON is slightly different (`0.8577`) and likely reflects a different/tuned artifact, but the repository does not provide a complete lineage tying that JSON to the exact current `best_model.pkl`. Do not claim that the final JSON is the exact post-tuning evaluation unless this is verified separately.

The README claims KNN + SMOTEENN at 98.08%, but KNN is not in the current `ModelFactory` or current comparison CSV, and SMOTEENN is only present in an older preprocessing notebook. This claim is therefore a documented legacy claim, not a verified current result.

## 7. Best Model

### Selected model

The current model-comparison implementation selects **Gradient Boosting** by holdout ROC-AUC. `ml_pipeline/models/best_model_info.json` and `best_params.json` identify Gradient Boosting as the selected/tuned model.

### Tuned hyperparameters in the repository

The saved `best_params.json` contains:

- `n_estimators = 433`
- `learning_rate = 0.020589728197687916`
- `max_depth = 2`
- `min_samples_split = 5`
- `min_samples_leaf = 4`
- `subsample = 0.8099025726528951`

The tuner used 100 Optuna trials, TPE sampling with seed `42`, a median pruner, and five-fold stratified ROC-AUC. It fitted the tuned model on `x_train.csv`/`y_train.csv` and overwrote `best_model.pkl`.

### Performance

The strongest directly persisted performance evidence is the final evaluation artifact: accuracy `0.8018`, precision `0.6450`, recall `0.5581`, F1 `0.5984`, and ROC-AUC `0.8577`, with confusion matrix `[[660, 82], [118, 149]]`. The comparison-table Gradient Boosting row reports ROC-AUC `0.8553`, so the artifact versions should be described as separate persisted results.

### What it predicts

It predicts binary churn class and a positive-class churn probability. The predictor maps probability to business risk:

- `>= 0.80`: Very High
- `>= 0.60`: High
- `>= 0.40`: Medium
- `>= 0.20`: Low
- `< 0.20`: Very Low

These thresholds are business labels in code, not an evaluated optimal threshold study.

## 8. Technical Implementation

### Important files and modules

| File or area | Purpose |
|---|---|
| `ml_pipeline/src/data_loader.py` | Load, clean, normalize, validate, target-encode, and save the dataset. |
| `ml_pipeline/src/preprocess.py` | Split, build/fit the `ColumnTransformer`, transform data, apply SMOTE, and save artifacts. |
| `ml_pipeline/src/feature_engineering.py` | Defines derived tenure, charge-per-tenure, and service-count features; not wired into current preprocessing. |
| `ml_pipeline/src/model_config.py` | Model factory, supported model names, defaults, and Optuna search spaces. |
| `ml_pipeline/src/train_model.py` | Train all available models, evaluate, cross-validate, select, and persist the best model. |
| `ml_pipeline/src/tune_model.py` | Optuna tuning of the selected model. |
| `ml_pipeline/src/predict.py` | Load artifacts, transform new input, predict class/probability/risk, and save batch results. |
| `ml_pipeline/src/evaluation.py` | Evaluation/reporting utilities. Exact invocation from the current production flow is **Not found in project**. |
| `ml_pipeline/src/revenue_risk.py` | Calculates CLV/revenue-risk and related retention-value outputs. |
| `ml_pipeline/src/shap_explainer.py` | Global/local SHAP explanation generation. |
| `ml_pipeline/src/recommendation_engine.py` | Deterministic rules-based retention recommendations. |
| `ml_pipeline/models/` | Saved model, preprocessing artifacts, metrics, parameters, feature importance, and tuning artifacts. |
| `backend/app/main.py` | Current FastAPI application and active route registration. |
| `backend/app/services/prediction_service.py` | Wraps `ChurnPredictor` for API use and reads saved predictions. |
| `backend/app/api/` | Authentication, imports, prediction, workspace, analytics, revenue, SHAP, recommendations, interactions, and retention workflow routes. |
| `backend/app/core/` | Configuration, security, tenancy, startup, and rate limiting. |
| `backend/app/database/` | SQLAlchemy/session, migrations, and database models. |
| `backend/app/schemas/` | Pydantic request/response schemas. |
| `dashboard/app.py` and `dashboard/pages/` | Streamlit executive dashboard, analytics, prediction, recommendations, revenue risk, SHAP, and what-if pages. |
| `frontend/src/` | React/Vite B2B application, routes, views, services, and styling. |
| `database/` | Legacy schema, seed, analytical SQL, and stored procedures. |
| `database/migrations/` | Identity, multitenancy, governance, and retention-workflow schema migrations. |
| `docker/` | Dockerfiles, Compose files, and Nginx configuration. |
| `.github/workflows/ci.yml` | CI workflow; frontend build runs, backend tests are currently a placeholder. |
| `requirements*.txt` and `frontend/package.json` | Dependency declarations. |
| `Data/` | Raw, cleaned, transformed, and SMOTE-resampled CSVs. |
| `reports/` | Evaluation, confusion matrix, classification, risk, recommendation, feature, and SHAP outputs. |

### Notebooks

- `EDA.ipynb`: EDA and written findings.
- `preprocessing.ipynb`: older label encoding, one-hot encoding, scaling, SMOTE, and SMOTEENN workflow.
- `Modling.ipynb`: older model comparison including KNN and Naive Bayes.
- `SHAP_Analysis.ipynb`: empty.
- `t_Business_insights.ipynb`: empty.

The older notebooks contain stale absolute Windows paths and conflicting result collection in places. Their values must not be presented as current production metrics without re-running and validating them.

### Libraries demonstrated by code

Python code uses pandas, NumPy, scikit-learn, imbalanced-learn/SMOTE, joblib, Optuna, SHAP, FastAPI, Pydantic, SQLAlchemy-related backend code, and optional XGBoost, LightGBM, and CatBoost. The frontend uses React/Vite and the repository includes Streamlit dashboard code. Exact versions should be taken from dependency files when needed; a complete verified version matrix is **Not found in project**.

### Model and data files

Important persisted artifacts include `best_model.pkl`, `preprocessing_pipeline.pkl`, `feature_columns.pkl`, `model_metrics.csv`, `best_model_info.json`, `best_params.json`, `study.pkl`, `optimization_history.csv`, and feature-importance CSVs. Root-level `model_pipeline.py` and `model_pipeline.pkl` are legacy/additional artifacts; their relationship to the current `ml_pipeline` artifact is **Not found in project**.

## 9. End-to-End Pipeline

Interview answer:

**Raw Data -> Cleaning -> EDA -> Stratified Train/Test Split -> Training-only preprocessing -> One-hot/scaling -> Optional SMOTE artifact -> Model comparison -> Holdout and five-fold ROC-AUC evaluation -> Gradient Boosting selection -> Optional Optuna tuning -> Persisted model and pipeline -> Prediction.**

The actual implementation does not call the feature-engineering helper in the current preprocessing path. It also does not use a separate validation split. The current trainer loads the non-resampled transformed train files, even though resampled files are created.

## 10. Prediction Flow

1. A dictionary, DataFrame, CSV import, or existing workspace customer is provided.
2. `ChurnPredictor` loads `best_model.pkl`, `preprocessing_pipeline.pkl`, and optionally `feature_columns.pkl`.
3. Input columns `Churn`, `Churn_flag`, `Unnamed: 0`, and `customerID` are removed when present.
4. The saved `ColumnTransformer` imputes and transforms the raw feature values exactly through its fitted numeric/categorical branches.
5. The transformed rows are converted to the saved model feature space.
6. The model returns a class with `predict()` and a positive-class score with `predict_proba()` when available.
7. The probability is mapped to a five-level risk label using the fixed thresholds above.
8. The result includes the numeric prediction, rounded probability, risk level, and churn label.
9. Batch scoring adds `Prediction`, `Probability`, and `Risk_Level` columns and can save `reports/predictions.csv`.
10. The backend can store prediction records, input snapshots, model version, and revenue-at-risk values, then connect the record to the operational retention workflow.

The backend currently hardcodes model version `v2.0` when creating prediction records according to the audit of the active application. It does not derive the version from a model registry in the shown prediction service.

## 11. Challenges

These are challenges visible in the project, not invented interview stories.

| Problem | Why difficult | How project addressed it | Result/status |
|---|---|---|---|
| Mixed/missing input values | Service fields, blank `TotalCharges`, and missing target labels require different handling. | Normalization, numeric conversion/median fill, categorical imputers, and dropping missing targets. | A cleaned 5,042-row dataset is persisted. |
| Class imbalance | Churn is the minority class. | Stratification and a SMOTE-resampled artifact. | Resampled training artifact is balanced, but current trainer usage is not fully consistent. |
| Comparing different model families | Models have different nonlinear/linear behavior and probability support. | Factory builds nine models; trainer calculates common metrics and CV ROC-AUC. | Gradient Boosting ranks first by saved comparison holdout ROC-AUC. |
| Hyperparameter selection | Default settings may not be optimal. | Optuna TPE search over 100 trials and five-fold ROC-AUC. | Tuned parameters are saved; post-tuning holdout evaluation lineage is incomplete. |
| Explainability | Business users need more than a class label. | SHAP global/local explanations and feature-importance outputs. | Top SHAP features are persisted. |
| Turning scores into actions | A score alone does not define a retention workflow. | Rules-based recommendations, interactions, tasks, follow-ups, and outcomes. | Operational workflow exists; recommendation effectiveness is not experimentally evaluated. |
| Multiple application generations | Legacy global SQL/API/dashboard paths coexist with current multitenant application paths. | Current `main.py` registers the newer B2B routes. | Architecture is functional but historical files make the active path harder to audit. |

## 12. Limitations

- The raw file has 5,043 rows, while README documentation says 7,043; the reason is not documented.
- Current test/evaluation artifacts are not completely lineage-linked to the model overwritten by tuning.
- The tuner overwrites `best_model.pkl` without an obvious post-tuning holdout report.
- The current trainer loads non-resampled training files even though SMOTE output is generated.
- The feature-engineering helper is not wired into current preprocessing.
- Churn recall is about 55.8% in the final evaluation artifact, so about 44.2% of actual churn cases in that holdout were missed.
- Fixed probability thresholds are not shown to be optimized for retention cost or capacity.
- Recommendations are deterministic rules, not learned or outcome-evaluated interventions.
- Revenue-risk formulas differ: the ML report uses `MonthlyCharges * tenure`, while the operational backend formula uses `monthly_charges * 12 * probability` for prediction revenue risk.
- API model version is hardcoded as `v2.0` in the active workflow.
- Exact raw source citation, formal data dictionary, and full reproducible experiment manifest are **Not found in project**.
- ML unit-test coverage is absent; `ml_pipeline/tests` contains only `.gitkeep` according to the audit.
- CI does not actually run backend pytest tests; it contains a placeholder echo and builds the frontend.
- No verified drift monitoring, production calibration monitoring, threshold optimization, fairness analysis, or retraining trigger is present.
- Legacy notebooks use stale absolute paths and contain conflicting/older metrics.
- Production documentation lists MFA, billing, monitoring, backups, privacy controls, and CRM integration as future/incomplete work.

## 13. Future Improvements

### A. Improvements already supported or indicated by the project

These are indicated by existing modules, documentation, or artifacts but are not necessarily complete:

- Complete model promotion/versioning instead of hardcoding `v2.0`.
- Finish production monitoring, centralized logs, backups, and dependency scanning described in `DEPLOYMENT.md`.
- Use the retention outcomes already stored to measure recommendation and intervention effectiveness.
- Complete product items identified in the project documentation such as MFA, billing, CRM integration, privacy controls, and password reset.
- Consolidate legacy and current schema/API paths.
- Make CI execute backend tests as deployment documentation expects.

### B. New suggestions not currently implemented

- Re-run a fully reproducible experiment from raw data with a recorded commit/configuration, data hash, library versions, and artifact lineage.
- Decide explicitly whether model training should use SMOTE, class weights, or threshold optimization, and evaluate that choice on an untouched holdout.
- Add a post-tuning holdout evaluation and calibration report for the exact promoted artifact.
- Optimize the decision threshold using retention capacity and false-negative/false-positive business costs.
- Add automated data-schema, pipeline, and ML regression tests.
- Monitor data drift, prediction drift, calibration, subgroup performance, and realized churn over time.
- Perform fairness analysis across the available demographic fields before operational use.
- Use temporal validation if timestamped customer snapshots become available.
- Align revenue-risk calculations across the ML report and backend service.
- Evaluate whether the engineered features improve out-of-sample performance before wiring them into production.

## 14. Interview Questions and Answers

### A. Basic project questions

**Tell me about your project.**

I built a telecom customer-churn and retention platform. It cleans customer records, trains and compares classification models, selects Gradient Boosting by holdout ROC-AUC, produces churn probability and risk labels, and exposes the result through a FastAPI/React workflow and a Streamlit analytics dashboard. The platform also includes SHAP explanations, revenue-risk calculations, and rules-based retention actions.

**What problem does it solve?**

It helps identify customers likely to churn and prioritize retention activity using churn probability and revenue-risk information.

**Why customer churn prediction?**

The project is designed around the business cost of losing recurring telecom customers and the need to prioritize limited retention effort.

**What is churn?**

In this project, churn is the binary target represented by the `Churn` field and encoded as `Churn_flag`: `1` for `Yes` and `0` for `No`.

**What is the target variable?**

The model target is `Churn_flag`, derived from `Churn`.

### B. Dataset questions

**Which dataset did you use?**

The project uses `Data/raw/telco_churn.csv`. The repository does not provide a source citation beyond the file and project documentation.

**How many records and features?**

The raw file has 5,043 rows and 22 columns. One missing-target row is dropped, leaving 5,042 cleaned rows. The README says 7,043 customers and 21 features, which conflicts with the current CSV and should be acknowledged.

**What preprocessing did you perform?**

I removed duplicate rows, stripped object-column whitespace, normalized selected category values, converted and median-filled `TotalCharges`, removed missing target labels, encoded the target, dropped identifiers, split stratified 80/20, imputed numeric/categorical values, scaled numeric values, one-hot encoded categories, and created a separate SMOTE-resampled training artifact.

**How did you handle missing values?**

`TotalCharges` is converted to numeric and filled with its median during data cleaning. The reusable preprocessing pipeline uses median imputation for numeric values and most-frequent imputation for categorical values. Rows with missing churn labels are dropped.

**How did you handle categorical variables?**

The current pipeline uses most-frequent imputation followed by `OneHotEncoder(handle_unknown="ignore", sparse_output=False)`. The older preprocessing notebook also contains label-encoding and one-hot-encoding experiments, but those are not the current production path.

**Was the dataset imbalanced?**

Yes. The cleaned target has 3,706 class-0 rows and 1,336 class-1 rows. The code stratifies the split and creates a balanced SMOTE artifact with 2,964 rows per class.

### C. Machine Learning questions

**Which algorithms did you use?**

The current comparison includes Logistic Regression, Random Forest, Decision Tree, Gradient Boosting, AdaBoost, XGBoost, LightGBM, CatBoost, and calibrated SVM. The older modeling notebook also includes KNN and Naive Bayes, but they are not in the current factory comparison.

**Why these algorithms?**

The code compares linear, tree, boosting, kernel, and optional gradient-boosting implementations to measure different inductive biases on tabular data. A more specific business rationale for every candidate is not explicitly documented.

**Why was Gradient Boosting selected?**

`ModelTrainer` selects the highest holdout ROC-AUC. Gradient Boosting is first in `model_metrics.csv` with ROC-AUC 0.8553; the selected/tuned model metadata also identifies Gradient Boosting.

**What is overfitting?**

Overfitting is when a model learns training-specific patterns that do not generalize. This project uses a holdout test split, stratified cross-validation, constrained/tuned models, and separate preprocessing fit on training data, but a complete overfitting analysis is not persisted.

**How did you prevent overfitting?**

The verified controls are a holdout split, five-fold stratified CV, model hyperparameters, and an untouched test evaluation. The project does not document early stopping for the selected Gradient Boosting model.

**Why is accuracy not always sufficient?**

Churn is the minority class and missing a real churner can be costly. Accuracy can look acceptable while recall for churn is weak. The project therefore records precision, recall, F1, ROC-AUC, and the confusion matrix.

**Explain precision, recall, and F1.**

Precision is the fraction of predicted churners who actually churn. Recall is the fraction of actual churners detected. F1 is their harmonic mean. In the final persisted evaluation, churn precision is about 0.6450 and recall about 0.5581.

**What is ROC-AUC?**

ROC-AUC measures how well model scores rank positive cases above negative cases across thresholds. The trainer uses holdout ROC-AUC for model selection and five-fold training cross-validation for an additional estimate.

**Explain your confusion matrix.**

The persisted matrix is `[[660, 82], [118, 149]]`: 660 true non-churn predictions, 82 false churn predictions, 118 missed churners, and 149 detected churners.

### D. Technical/code questions

**Which class controls preprocessing?**

`Preprocessor` in `ml_pipeline/src/preprocess.py`. It loads the cleaned dataset, splits X/y, performs the stratified split, builds the `ColumnTransformer`, transforms data, applies SMOTE, and saves artifacts.

**Which class performs inference?**

`ChurnPredictor` in `ml_pipeline/src/predict.py`. It loads the model/pipeline, prepares raw input, transforms it, predicts class/probability, maps risk, and supports batch/CSV predictions.

**How are models constructed?**

`ModelFactory` in `model_config.py` exposes model names, default estimators, model creation with parameters, and Optuna parameter spaces.

**How does the backend call ML?**

`PredictionService` imports `ChurnPredictor`, constructs it, and delegates `predict(customer_data)`. API route modules use services and schemas around that behavior.

**What does the backend store?**

The current multitenant schema/application includes organizations, memberships, customers, organization-customer links, prediction records, tasks, interactions, playbooks, retention outcomes, imports, model versions, audit logs, and invitations.

**Why are there two dashboard/application surfaces?**

The repository has an artifact-driven Streamlit dashboard and a newer React/FastAPI B2B workspace. The active backend registration favors the B2B workflow, while the Streamlit pages read persisted ML/report artifacts directly.

### E. Scenario-based questions

**What would you do if the model predicts too many customers as churners?**

Inspect the confusion matrix and precision, check calibration and data drift, then evaluate a higher decision threshold against retention capacity and business costs. I would not change the threshold without measuring the tradeoff on a holdout.

**What if recall is low?**

Because missed churners are false negatives, I would inspect threshold curves, class weighting/resampling choices, feature quality, and subgroup performance. The current persisted recall is about 55.8%, so this is a real improvement area.

**What if the data becomes highly imbalanced?**

Use stratified splits, compare class weights with resampling, use PR-AUC and recall/precision at an operating threshold, and ensure resampling is applied only to training data. I would also verify which training artifact the trainer actually consumes.

**What if training performance is high but test performance is poor?**

That indicates overfitting or data shift. I would inspect train/CV/holdout gaps, reduce model complexity, improve validation design, check leakage, and validate the raw-to-feature pipeline.

**How would you deploy this model?**

The repository provides a FastAPI backend, React/Vite frontend, Streamlit dashboard, Docker Compose/Dockerfiles, and GitHub Actions workflow. I would package the exact model and preprocessing artifacts together, use environment secrets, run tests, and expose an authenticated prediction endpoint.

**How would you monitor it?**

The current project has live metrics/audit/workflow structures, but a complete ML monitoring implementation is not found. I would add input drift, score drift, calibration, realized churn, latency/error, subgroup metrics, and model-version tracking.

## 15. Difficult Follow-up Questions

**Why Gradient Boosting instead of Random Forest?**

Because the current selector uses holdout ROC-AUC and Gradient Boosting scored 0.8553 versus Random Forest at 0.8467 in `model_metrics.csv`. Random Forest had higher accuracy, 0.8038 versus 0.7998, so the choice reflects the selected metric rather than maximum accuracy.

**Why not choose Logistic Regression, which had higher recall?**

Logistic Regression recall was 0.8202, but its accuracy was 0.7384 and ROC-AUC was 0.8513. The implemented selector prioritizes ROC-AUC, not recall alone. If the business cost of missed churn were higher, I would evaluate threshold and cost-sensitive selection explicitly.

**Why use one-hot encoding?**

The current features are categorical strings. One-hot encoding converts them to numeric columns without imposing an artificial ordering, and `handle_unknown="ignore"` supports unseen categories during inference.

**Why scale numeric features?**

Scaling puts `tenure`, `MonthlyCharges`, and `TotalCharges` on comparable numeric scales and is particularly useful for Logistic Regression and SVM. Tree models are less dependent on scaling, but the shared preprocessing pipeline standardizes all numeric candidates.

**Why use SMOTE?**

The target is imbalanced. SMOTE creates synthetic minority training examples. In this repository it is persisted as a separate artifact, but the current trainer reads the non-resampled train files, so I would verify or correct that workflow before claiming the selected model was trained with SMOTE.

**What happens internally during prediction?**

The saved pipeline applies its fitted numeric and categorical transformations, producing the same 41-column transformed feature space expected by the saved estimator. The estimator returns a class and positive-class probability, and code maps the probability to the configured risk band.

**What if one feature is removed?**

The persisted preprocessing pipeline and estimator expect their trained schema. Removing a required raw input may cause a transformation error or alter the feature representation. I would retrain and reevaluate with that feature removed rather than deleting it only at inference.

**How do you know the model is not overfitting?**

The project compares holdout and five-fold ROC-AUC and keeps the test split untouched during preprocessing fitting. However, a complete train-versus-test diagnostic and post-tuning holdout evaluation are not fully persisted, so I should describe overfitting control as partial rather than proven.

**What would you improve first?**

First I would make artifact lineage reproducible: align raw row counts, preprocessing/SMOTE usage, tuned model, evaluation metrics, and model version. Then I would optimize threshold and monitor churn recall/calibration against business cost.

**What would change with more data?**

I would use new customer snapshots and, if available, time-based validation to test generalization over time. I would also re-check missingness, category drift, calibration, subgroup performance, and whether engineered features add value.

**Why do README and artifacts disagree?**

The repository contains legacy notebook and documentation claims alongside a newer source/artifact pipeline. The README's KNN/SMOTEENN/98.08% claim is not reproduced by the current model factory or comparison CSV, so I would treat it as stale until rerun.

## 16. 60-Second Project Explanation

I built a telecom customer-churn prediction and retention platform. The raw CSV contains customer demographics, service subscriptions, contract, billing, tenure, and a churn label. I cleaned duplicates and inconsistent categories, converted `TotalCharges`, handled missing values, removed identifiers, and used a stratified 80/20 split. A scikit-learn `ColumnTransformer` imputes values, scales numeric fields, and one-hot encodes categorical fields. I compared nine classifiers and selected Gradient Boosting using holdout ROC-AUC. The saved evaluation reports about 80.2% accuracy and 0.8577 ROC-AUC, with churn recall around 55.8%. The model returns a probability and risk band. FastAPI exposes predictions, while the React workspace and Streamlit dashboard support risk queues, revenue risk, SHAP explanations, and retention actions. The main caveats are artifact lineage, the dataset-size documentation mismatch, and the need for better recall and monitoring.

## 17. 2-Minute Project Explanation

The project addresses telecom customer churn by predicting which customers are likely to leave and connecting the prediction to a retention workflow. The raw project file is `Data/raw/telco_churn.csv`; the actual repository copy contains 5,043 rows and 22 columns. It includes customer demographics, tenure, services, contract, payment method, monthly charges, total charges, and the `Churn` label. One row has a missing churn label, so the cleaned dataset has 5,042 rows. The target is encoded as `Churn_flag`, with 3,706 non-churn and 1,336 churn records.

The data loader removes duplicate rows, trims strings, normalizes selected service values, converts `TotalCharges` to numeric, fills its missing values with the median, and drops missing target labels. The preprocessor drops identifiers, creates an 80/20 stratified split with random state 42, fits a training-only `ColumnTransformer`, uses median and most-frequent imputers, standardizes numeric columns, and one-hot encodes categorical columns. It also creates a SMOTE-resampled artifact, although the current trainer reads the non-resampled transformed files.

The current model factory compares Logistic Regression, Random Forest, Decision Tree, Gradient Boosting, AdaBoost, XGBoost, LightGBM, CatBoost, and calibrated SVM. The trainer reports accuracy, precision, recall, F1, ROC-AUC, confusion matrix, and five-fold ROC-AUC. Gradient Boosting is selected by holdout ROC-AUC; its comparison value is 0.8553. The separate persisted final evaluation reports 0.8018 accuracy, 0.6450 precision, 0.5581 recall, 0.5984 F1, and 0.8577 ROC-AUC. The confusion matrix contains 149 detected churners and 118 missed churners.

For inference, the saved preprocessing pipeline transforms a new customer, the saved model returns a class and probability, and code maps that probability into Very Low through Very High risk. The FastAPI backend stores prediction and retention-workflow records; the React app supports the B2B workspace; and Streamlit provides analytics, revenue-risk, recommendations, SHAP, and what-if pages. The business impact intended by the project is better prioritization of retention work and visibility into revenue at risk. A measured reduction in churn or protected revenue is not found in project evidence.

## 18. Resume-Based Questions

- You mention churn prediction. What exactly is the target and how was it encoded?
- Your resume says end-to-end. Which file controls preprocessing and which controls inference?
- Why does your README report 7,043 customers while the current raw file has 5,043 rows?
- Why did you choose Gradient Boosting when Random Forest had higher accuracy?
- What does your 55.8% churn recall mean operationally?
- Did the current model actually train on the SMOTE-resampled data?
- How did you prevent preprocessing leakage?
- What are the 41 transformed features?
- How does a raw API request reach the persisted model?
- How did you calculate revenue at risk?
- Why are the ML and backend revenue-risk formulas different?
- What does SHAP add beyond feature importance?
- How are recommendations generated?
- What tests validate your backend and ML pipeline?
- How would you monitor this model after deployment?

## 19. Skills I Can Claim From This Project

### Programming

- Python
- JavaScript/React
- SQL

### Data preprocessing

- pandas data loading and cleaning
- Missing-value imputation
- Duplicate removal
- Numeric conversion
- One-hot encoding
- Standard scaling
- Stratified train/test splitting
- SMOTE resampling
- scikit-learn `Pipeline` and `ColumnTransformer`

### EDA

- Dataset summaries and missing-value analysis
- Numeric summaries
- Histograms and boxplots
- Categorical churn comparisons
- Correlation heatmaps
- Business interpretation of churn segments

### Machine Learning

- Binary classification
- Logistic Regression
- Decision Trees and Random Forest
- Gradient Boosting and AdaBoost
- XGBoost, LightGBM, CatBoost
- SVM calibration
- ROC-AUC, accuracy, precision, recall, F1
- Confusion matrices
- Stratified cross-validation
- Optuna hyperparameter optimization
- SHAP explainability
- Probability-based risk bands

### Libraries

- pandas
- NumPy
- scikit-learn
- imbalanced-learn
- joblib
- Optuna
- SHAP
- FastAPI
- Pydantic
- Streamlit
- React/Vite ecosystem
- Optional XGBoost, LightGBM, and CatBoost packages used by the model factory

### Deployment/API

- FastAPI REST API code
- Uvicorn configuration in project docs
- Docker and Docker Compose
- Nginx configuration in deployment files
- GitHub Actions workflow
- Authentication, bearer/cookie tokens, CORS, and tenant-aware backend code

### Database

- PostgreSQL-oriented schema and SQL
- SQL migrations
- Analytical SQL queries
- SQLAlchemy/session/model code in the backend
- Multi-tenant entities and audit records

### Tools

- Jupyter notebooks
- VS Code workspace
- GitHub Actions
- Docker
- CSV/JSON/PKL model artifacts

Technologies merely present in dependency/environment folders but not demonstrated by project code should not be claimed. Azure use is described in documentation/configuration context, but a verified deployed Azure service is **Not found in project**.

## 20. Final Interview Cheat Sheet

- **Objective:** Predict telecom customer churn and support retention prioritization.
- **Raw dataset:** `5,043 x 22`; cleaned dataset: `5,042` rows.
- **Features:** Demographics, tenure, phone/internet/services, contract, billing/payment, and total charges.
- **Target:** `Churn_flag`; `1 = Yes`, `0 = No`.
- **Cleaned target:** 3,706 class 0; 1,336 class 1.
- **Preprocessing:** Drop identifiers, normalize categories, convert/fill `TotalCharges`, stratified 80/20 split, median/most-frequent imputation, standard scaling, one-hot encoding.
- **Resampling:** SMOTE artifact has 2,964 examples per class, but current trainer reads non-resampled train files.
- **Models:** Logistic Regression, Random Forest, Decision Tree, Gradient Boosting, AdaBoost, XGBoost, LightGBM, CatBoost, calibrated SVM.
- **Best selection rule:** Highest holdout ROC-AUC.
- **Selected model:** Gradient Boosting.
- **Comparison ROC-AUC:** 0.8553.
- **Final persisted evaluation:** Accuracy 0.8018; precision 0.6450; recall 0.5581; F1 0.5984; ROC-AUC 0.8577.
- **Confusion matrix:** TN 660, FP 82, FN 118, TP 149.
- **EDA findings:** Short tenure, month-to-month contracts, fiber optic, senior-citizen status, electronic check, and absent support/security services are associated with higher churn.
- **Main challenge:** Inconsistent data/artifact generations and incomplete lineage between tuning and final evaluation.
- **Main limitation:** Churn recall is only about 55.8% in the final persisted evaluation, and post-tuning validation is incomplete.
- **Tech stack:** Python, pandas, NumPy, scikit-learn, imbalanced-learn, Optuna, SHAP, FastAPI, React/Vite, Streamlit, SQL/PostgreSQL-oriented backend, Docker, GitHub Actions.

### Ten important questions

1. What is the target and how is it encoded?
2. How many rows are actually in the raw file?
3. How did you prevent preprocessing leakage?
4. Why did you use stratification?
5. Did the trainer use the SMOTE data?
6. Why was Gradient Boosting selected?
7. What does the confusion matrix mean?
8. Why is churn recall important?
9. How does a new API input reach the model?
10. What would you improve before production?

## 21. Fact Check Section

### PROJECT FACTS I MUST MEMORIZE

- The raw file is `Data/raw/telco_churn.csv`.
- The current raw file has 5,043 rows and 22 columns.
- The cleaned dataset has 5,042 rows because one missing churn label is removed.
- The cleaned target counts are 3,706 non-churn and 1,336 churn.
- The target is `Churn_flag`, derived from `Churn` as `Yes=1`, `No=0`.
- The split is stratified 80/20 with random state 42.
- Numeric preprocessing uses median imputation and `StandardScaler`.
- Categorical preprocessing uses most-frequent imputation and one-hot encoding with unknown categories ignored.
- The processed split has 4,033 training rows and 1,009 test rows.
- The SMOTE artifact has 5,928 rows, balanced at 2,964 per class.
- The current trainer loads the non-resampled processed train files.
- The current model factory comparison includes nine model names: Logistic Regression, Random Forest, Decision Tree, Gradient Boosting, AdaBoost, XGBoost, LightGBM, CatBoost, and SVM.
- The comparison selector uses holdout ROC-AUC.
- Gradient Boosting is the selected model in current metadata/comparison artifacts.
- The tuned Gradient Boosting parameters are persisted in `ml_pipeline/models/best_params.json`.
- The final evaluation JSON reports accuracy 0.8017839444995044 and ROC-AUC 0.857715759613152.
- The final confusion matrix is TN 660, FP 82, FN 118, TP 149.
- The current predictor returns class, probability, prediction label, and five-level risk label.
- SHAP, revenue-risk, rules-based recommendations, FastAPI, React, and Streamlit components exist in the repository.

### INFORMATION NOT FOUND / NEEDS VERIFICATION

- The external/public source citation for the raw dataset.
- Why README says 7,043 customers while the current raw file has 5,043 rows.
- A formal data dictionary with authoritative definitions for every feature.
- A saved raw-data EDA output containing every exact summary statistic and visualization value.
- Whether the persisted final evaluation JSON was generated from the exact tuned `best_model.pkl` currently present.
- A post-tuning holdout evaluation tied to the promoted model artifact.
- Confirmation that the current production model was trained on SMOTE data; current trainer code indicates it reads non-resampled files.
- A verified measured business impact such as churn reduction, retention uplift, or causal revenue saved.
- A fully reproducible model/artifact lineage and version registry flow.
- Exact dependency versions as a single verified environment manifest.
- ML unit tests and complete backend CI test execution.
- Production drift monitoring, calibration monitoring, threshold optimization, and fairness results.
- A verified Azure deployment.
- The relationship between root-level `model_pipeline.pkl` and the current `ml_pipeline/models/best_model.pkl`.
- Exact numeric EDA statistics beyond the persisted metrics and CSV counts.

## Report verification note

This report was created as a new file at `interview_preparation/customer_churn_interview_report.md`. Existing project files were not modified, deleted, renamed, or overwritten. Metrics in the report are copied from persisted project artifacts or calculated directly from the repository CSV files; conflicting README/notebook claims are explicitly labeled as legacy or needing verification.
