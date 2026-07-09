# 🧠 Decision Intelligence Platform

An end-to-end AI-powered platform for **Customer Churn Prediction** and **Revenue Risk Analysis** in the telecom domain.

---

## 🏗️ Architecture

```
Decision-Intelligence-Platform/
├── frontend/          # React + Vite + Recharts
├── backend/           # FastAPI REST API
├── ml_pipeline/       # ML training & inference
├── dashboard/         # Streamlit dashboard
├── database/          # PostgreSQL schema & queries
├── data/              # Raw, processed, resampled data
├── docker/            # Docker & docker-compose
├── deployment/        # CI/CD & Azure configs
└── docs/              # Architecture & API docs
```

---

## 🚀 Quick Start

### Option 1 — Docker (Full Stack)
```bash
cd docker
docker-compose up --build
```
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- Streamlit Dashboard: http://localhost:8501
- API Docs: http://localhost:8000/docs

### Option 2 — Manual

**ML Pipeline:**
```bash
cd ml_pipeline
pip install -r ../requirements.txt
python src/train_model.py
```

**Backend:**
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

**Dashboard:**
```bash
pip install -r requirements-app.txt
streamlit run dashboard/app.py
```

---

## 🤖 ML Models

| Model | Accuracy |
|---|---|
| KNN + SMOTEENN | **98.08%** |
| SVM | >96% |
| XGBoost | >96% |
| Gradient Boosting | >96% |

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 18, Vite, Recharts, React Router |
| Backend | FastAPI, Pydantic, Uvicorn |
| ML | scikit-learn, XGBoost, LightGBM, CatBoost, SHAP |
| Dashboard | Streamlit |
| Database | PostgreSQL |
| Deployment | Docker, GitHub Actions, Azure |

---

## 📊 Key Features

- Single & batch churn prediction
- SHAP explainability (global + local)
- Revenue risk analysis by segment
- Rules-based retention recommendations
- What-If scenario simulation
- Executive KPI dashboard
- SQL analytical insights

---

## 📁 Dataset

Telecom customer churn dataset with 7,043 customers and 21 features including demographics, services, and billing information.
