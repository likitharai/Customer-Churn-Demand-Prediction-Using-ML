# 🧠 RetainIQ — Customer Churn Prediction & Retention Platform

An end-to-end B2B Decision Intelligence Platform for **Customer Churn Prediction**, **Operational Revenue Risk Management**, and **Automated Retention Playbooks**.

---

## 📌 Architecture Overview

RetainIQ combines a leakage-free machine learning inference pipeline with an enterprise multi-tenant SaaS backend and interactive web interface:

```
Customer-Churn-Demand-Prediction-Using-ML/
├── backend/                  # FastAPI REST API with multi-tenancy & auth
│   ├── app/
│   │   ├── api/              # Role-based endpoints (agent, manager, admin, workspace)
│   │   ├── core/             # Tenancy context, JWT security, configuration
│   │   ├── database/         # SQLAlchemy models (customers, orgs, predictions, tasks)
│   │   └── services/         # Prediction service, deterministic retention engine, business rules
│   └── tests/                # Pytest unit & integration test suite (27 tests)
├── frontend/                 # React 18 + Vite + Tailwind/Recharts client
├── dashboard/                # Standalone Streamlit exploratory analytics dashboard
├── database/                 # PostgreSQL relational schema and seed scripts
├── Data/                     # Cleaned telco dataset (5,042 records) and processed splits
├── reports/                  # Authoritative model release metadata, metrics, and SHAP artifacts
├── docker/                   # Docker Compose setup (Frontend, Backend, PostgreSQL)
├── model_pipeline.py         # Authoritative training, validation, and evaluation pipeline
└── model_pipeline.pkl        # Authoritative serialized LightGBM production pipeline
```

---

## 🤖 Authoritative Machine Learning Release (v1.0.0)

All inference, API scoring, and business logic are powered by the authoritative release artifact `model_pipeline.pkl`.

### Performance & Validation (Holdout Test Set)

The model was trained strictly on an 80% split (4,033 customers) and evaluated on an untouched 20% holdout test set (1,009 customers) with zero data leakage:

| Metric | Holdout Value | Validation Notes |
|---|---|---|
| **ROC-AUC** | **0.8563** | 5-Fold Cross-Validation ROC-AUC: **0.8480 ± 0.0098** |
| **Recall (Churners)** | **82.77%** | Catches 221 of 267 at-risk customers (46 false negatives) |
| **PR-AUC** | **0.6711** | High precision-recall area on minority class (26.5% base rate) |
| **F1 Score** | **0.6296** | Balanced harmonic mean under cost-sensitive weighting |
| **Accuracy** | **74.23%** | Prioritizes recall to minimize unaddressed churn revenue loss |
| **Precision** | **50.80%** | Standard for cost-sensitive retention outreach |
| **Log Loss** | **0.4771** | Well-calibrated class probability output |

### Audit Clarification Regarding Historical Claims
- **Historical 98.08% Claim**: Legacy exploratory notebooks contained severe data leakage (applying SMOTEENN and StandardScaler to the full dataset before splitting). Synthetic samples bled into test sets, creating artificially inflated accuracy.
- **Production Standard**: The active pipeline adheres to strict ML hygiene — data is split *before* any transformation, transformers are fitted solely on training splits, and cost-sensitive class weighting (`class_weight='balanced'`) is used instead of synthetic oversampling.

### Confusion Matrix (1,009 Test Samples)
```
                  Predicted Retained (0)   Predicted Churned (1)
Actual Retained (0)        528                     214
Actual Churned (1)          46                     221
```

---

## 🏢 Multi-Tenant Enterprise Features

- **Organization Isolation**: Every customer, prediction record, retention task, and interaction is strictly partitioned by `organization_id`.
- **Role-Based Access Control (RBAC)**:
  - **Agents**: Assigned customer risk queues, task completion, interaction logging.
  - **Managers**: Team workload analytics, manual re-assignment, playbook creation.
  - **Admins**: Workspace configuration, user invitations, audit log review.
- **Deterministic Retention Engine**: Rules-based playbooks providing auditable, explainable actions (contract upgrade proposals, tech support bundles, loyalty incentives).
- **Revenue Risk Quantification**:
  $$\text{Monthly Revenue At Risk} = \text{MonthlyCharges} \times P(\text{Churn})$$
  $$\text{Annual Priority Score} = P(\text{Churn}) \times \text{MonthlyCharges} \times 12$$

---

## 🚀 Running the Project

### 1. Docker Compose (Full Stack)
The Docker Compose configuration launches the primary platform services:
```bash
cd docker
docker-compose up --build
```
- **Frontend SPA**: `http://localhost:3000`
- **FastAPI Backend**: `http://localhost:8000`
- **Interactive API Docs**: `http://localhost:8000/docs`
- **PostgreSQL**: Port 5433 (host) -> 5432 (container)

### 2. Local Manual Startup

**Train / Evaluate Authoritative Model:**
```bash
python model_pipeline.py
```
*Outputs `model_pipeline.pkl`, `reports/model_release.json`, and `reports/evaluation_metrics.json`.*

**Run Backend API:**
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

**Run Backend Test Suite:**
```bash
python -m pytest backend/tests -v
```
*(All 27 unit tests pass, covering production config, security, risk rules, ML inference, and tenancy).*

**Run Frontend:**
```bash
cd frontend
npm install
npm run dev
```

**Run Exploratory Streamlit Dashboard (Optional Analytics Tool):**
```bash
pip install -r requirements-app.txt
streamlit run dashboard/app.py
```

---

## 📋 Technology Stack

| Layer | Technologies |
|---|---|
| **Machine Learning** | LightGBM, scikit-learn, joblib, pandas, NumPy, SHAP |
| **Backend API** | FastAPI, Pydantic, SQLAlchemy 2.0, Uvicorn, Python 3.10 |
| **Security & Auth** | JWT Tokens (HS256), Passlib (PBKDF2/Bcrypt), Tenancy Context |
| **Frontend UI** | React 18, Vite, Lucide Icons, Recharts, Tailwind CSS |
| **Database** | PostgreSQL 15 (Docker) / SQLite (in-memory test harness) |
| **Testing & CI** | Pytest, Ruff, GitHub Actions CI |
