# RETAINIQ — PRODUCTION DEPLOYMENT & VERIFICATION REPORT

**Repository**: `https://github.com/likitharai/Customer-Churn-Demand-Prediction-Using-ML`  
**Branch**: `main` (Commit `ba935d7`)  
**Deployment Target**: GitHub Repository & Render Cloud Blueprint (`render.yaml`)  
**Timestamp**: 2026-10-03 00:50:00 UTC+05:30  
**Status**: **DEPLOYED TO GITHUB / READY FOR RENDER BLUEPRINT ONE-CLICK LAUNCH**

---

## 1. DEPLOYMENT ARCHITECTURE

The RetainIQ Decision Intelligence Platform is structured as a modern cloud-native 3-tier architecture:
1. **Frontend Tier**: React 18 Single-Page Application (SPA) bundled via Vite 5.
   - Built to static assets in `dist/`.
   - Routing: Single-page routing with rewrites (`/*` $\rightarrow$ `/index.html`) via `render.yaml` and `frontend/vercel.json`.
2. **Backend Tier**: High-performance FastAPI application.
   - Entry point: `app.main:app` running via Uvicorn.
   - Automated startup lifespan: Environment hardening check (`validate_environment()`), database table creation (`Base.metadata.create_all`), migration runner (`run_migrations()`), and default admin/playbook seeding.
3. **Database Tier**: Managed PostgreSQL database (`retainiq-db`).
   - Multi-tenant relational schema: `organizations`, `memberships`, `users`, `customers`, `organization_customers`, `prediction_records`, `retention_playbooks`, `tenant_interactions`.
4. **Machine Learning Tier**:
   - Authoritative model: **LightGBM Pipeline `v1.0.0`** (`model_pipeline.pkl`).
   - Inference Engine: `ChurnPredictor` and `PredictionService` providing real-time inference, risk tier classification, tailored recommendations, and revenue-at-risk calculations.

---

## 2. SERVICES & DEPLOYMENT TARGETS

| Target / Service | Type | Source Path / Artifact | Current Status |
| :--- | :--- | :--- | :--- |
| **GitHub Remote** | Source Control / CI | `github.com/likitharai/...` | ✅ **Fully Pushed (`main` up to date)** |
| **GitHub Actions CI** | CI Pipeline | `.github/workflows/ci.yml` | ✅ **Active & Passing** |
| **Render Database** | Managed PostgreSQL | `retainiq-db` in `render.yaml` | ⏳ Configured in Blueprint (Ready for Web UI Launch) |
| **Render Backend** | Python Web Service | `retainiq-backend` in `render.yaml`| ⏳ Configured in Blueprint (Ready for Web UI Launch) |
| **Render Frontend** | Static Site Service | `retainiq-frontend` in `render.yaml`| ⏳ Configured in Blueprint (Ready for Web UI Launch) |

---

## 3. VERIFICATION & TEST EVIDENCE

### A. Backend Test Suite (Pytest)
- Command: `python -m pytest backend/tests -v`
- Result: **28 passed out of 28 tests in 7.65s (100% Pass Rate)**.
- Modules Verified:
  - `test_ml_pipeline.py`: Pipeline loading, prediction schema, risk monotonicity, missing feature imputation.
  - `test_production_config.py`: Hardened environment configs, secret validation, weak default rejection.
  - `test_recommendation_engine.py`: Deterministic rule-based recommendations.
  - `test_retention_rules.py`: Risk clamping, probability adjustments, interaction history.
  - `test_revenue_and_risk.py`: Revenue-at-risk ($\text{MonthlyCharges} \times P$), priority score ($\text{Charges} \times P \times 12$), CLV, and risk thresholds.
  - `test_security.py`: Password hashing with PBKDF2/Argon2, JWT signing, identity verification.
  - `test_tenancy.py`: Strict cross-tenant database isolation, role-based access control, active workspace validation.

### B. Frontend Production Build
- Command: `npm run build` (in `frontend/`)
- Result: **Vite build succeeded cleanly in 8.75s**.
- Artifacts:
  - `dist/index.html` (0.62 kB)
  - `dist/assets/index-B71vo9ZK.css` (23.89 kB)
  - `dist/assets/index-Bo0YV9gV.js` (615.17 kB)

### C. End-to-End Production Smoke Test
- Command: `python scratch/test_production_smoke.py`
- Result: **100% Passed (8 out of 8 assertions verified)**:
  - `GET /` $\rightarrow$ `200 OK`
  - `GET /api/health/` $\rightarrow$ `200 OK` (`status: healthy`, `model_loaded: true`, `model_version: v1.0.0`)
  - Inference: Customer scored with $P=0.9503$, Risk: Very High, 5 tailored recommendations generated.
  - Multi-tenant data segregation verified.

---

## 4. SECURITY & CONFIGURATION AUDIT

- **Hardcoded Secrets**: Verified 0 hardcoded passwords, tokens, or JWT secrets in production code.
- **Environment Validation**: `validate_environment()` in `backend/app/core/config.py` enforces minimum 32-character `TOKEN_SECRET`, minimum 12-character `ADMIN_PASSWORD`, PostgreSQL database URI, and HTTPS CORS origins in production.
- **Old Pipeline Purge**: Verified 0 references to deleted `ml_pipeline.src`.
- **External Data Purge**: Exploratory external CSVs permanently deleted; `Data/external/*.csv` added to `.gitignore`.

---

## 5. RENDER CLOUD BLUEPRINT ONE-CLICK LAUNCH INSTRUCTIONS

Because Render uses interactive OAuth to connect GitHub accounts, trigger the cloud launch from Render's dashboard:

1. Log in to [dashboard.render.com](https://dashboard.render.com).
2. Click **New +** $\rightarrow$ **Blueprint**.
3. Select repository: `likitharai/Customer-Churn-Demand-Prediction-Using-ML`.
4. Render automatically parses `render.yaml` and provisions:
   - PostgreSQL Database `retainiq-db`
   - FastAPI Backend `retainiq-backend` (installs `backend/requirements.txt`, applies migrations, loads model)
   - React Frontend `retainiq-frontend` (builds Vite bundle to `dist`)
5. Once live, Render assigns public URLs:
   - Backend: `https://retainiq-backend.onrender.com`
   - Frontend: `https://retainiq-frontend.onrender.com`
   - Health: `https://retainiq-backend.onrender.com/api/health/`
