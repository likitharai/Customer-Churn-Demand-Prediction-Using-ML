# RetainIQ Cloud & Production Deployment Guide

This guide details the deployment of the RetainIQ B2B platform:
- **FastAPI Backend** (`/api`, `/api/health`, `/api/auth`, `/api/workspace`)
- **React 18 + Vite Frontend** (`frontend/dist`)
- **PostgreSQL 15 Relational Database**
- **Authoritative ML Pipeline** (`model_pipeline.pkl`, LightGBM v1.0.0)

---

## ☁️ Free & Low-Cost Cloud Architecture Comparison

| Cloud Provider | Architecture Components | Free Tier Status & Quotas | Potential Cost Traps / Warnings |
|---|---|---|---|
| **Render + Neon / Supabase** *(Recommended for Zero-Cost)* | • Frontend: Render Static Site<br>• Backend: Render Web Service<br>• DB: Neon / Supabase Serverless PG | **100% Free Forever**<br>• 512 MB RAM Web Service<br>• 500 MB DB storage<br>• Free custom domains & SSL | Web Service spins down after 15 mins of inactivity; 50s cold start on first request. |
| **Microsoft Azure** | • Frontend: Azure Static Web Apps<br>• Backend: Azure App Service (Linux F1)<br>• DB: Neon PostgreSQL (or Azure PG Flexible) | **Free with Limits**<br>• SWA: Free tier (100 GB/mo)<br>• F1: 60 CPU min/day, 1 GB RAM<br>• Azure PG is **NOT free** (use external free DB or $100 student credit) | Azure Database for PostgreSQL Flexible Server costs ~$12-15/month after trial. Use Neon/Supabase for DB to stay 100% free. |
| **Amazon Web Services (AWS)** | • Frontend: AWS S3 + CloudFront<br>• Backend: AWS App Runner / EC2 `t4g.small`<br>• DB: AWS RDS PostgreSQL `db.t4g.micro` | **12-Month Free Tier**<br>• 750 hrs/mo EC2/RDS for 12 mos<br>• 1 TB/mo CloudFront free | **High Risk**: Configuring a VPC NAT Gateway or Application Load Balancer (ALB) immediately incurs ~$32/month. AWS charges $3.60/mo for public IPv4s. |

---

## 🚀 Option 1: Render + Neon/Supabase (100% Free, Zero Bill Shock)

Render provides native support via the checked-in [`render.yaml`](file:///c:/Users/raich/Desktop/decision/Customer-Churn-Demand-Prediction-Using-ML/render.yaml) blueprint:

### 1. Database Setup (Neon or Supabase)
1. Sign up at [neon.tech](https://neon.tech) or [supabase.com](https://supabase.com).
2. Create a free project named `retainiq-prod`.
3. Copy the pooled PostgreSQL connection string:
   ```
   postgresql+psycopg://username:password@ep-sample.us-east-2.aws.neon.tech/neondb?sslmode=require
   ```

### 2. Deploy via Render Blueprint
1. Fork or push this repository to GitHub.
2. Log into [dashboard.render.com](https://dashboard.render.com) and click **New +** $\rightarrow$ **Blueprint**.
3. Connect your repository. Render automatically reads `render.yaml`.
4. Fill in environment variables:
   - `DATABASE_URL`: Your Neon/Supabase connection string.
   - `TOKEN_SECRET`: A 64-character random string (e.g. `openssl rand -hex 32`).
   - `ADMIN_EMAIL`: `admin@retainiq.internal`
   - `ADMIN_PASSWORD`: A secure password (minimum 12 chars).
5. Click **Apply**. Render builds both the FastAPI service and the React static site.

---

## 🏢 Option 2: Microsoft Azure Deployment

### 1. Frontend: Azure Static Web Apps (Free Tier)
```bash
az staticwebapp create \
  --name retainiq-frontend \
  --resource-group RetainIQ-RG \
  --source https://github.com/<your-org>/<repo> \
  --location "eastus2" \
  --branch "main" \
  --app-location "/frontend" \
  --output-location "dist"
```

### 2. Backend: Azure App Service (Linux F1 Free)
```bash
# Create App Service Plan (Free F1 tier)
az appservice plan create \
  --name retainiq-plan \
  --resource-group RetainIQ-RG \
  --sku F1 \
  --is-linux

# Create Web App
az webapp create \
  --resource-group RetainIQ-RG \
  --plan retainiq-plan \
  --name retainiq-api \
  --runtime "PYTHON:3.10"

# Configure Environment Variables
az webapp config appsettings set \
  --resource-group RetainIQ-RG \
  --name retainiq-api \
  --settings \
    APP_ENV="production" \
    DATABASE_URL="<your-neon-postgres-url>" \
    TOKEN_SECRET="<random-64-char-secret>" \
    ADMIN_EMAIL="admin@retainiq.internal" \
    ADMIN_PASSWORD="<secure-password>" \
    CORS_ORIGINS="https://retainiq-frontend.azurestaticapps.net" \
    PORT="8000"
```

---

## 📦 Option 3: Self-Hosted Docker Compose (Local / VPS)

For a self-contained private deployment on a Virtual Private Server (Hetzner, DigitalOcean, Linode):

```bash
# 1. Create .env file with production secrets
cp .env.example .env

# 2. Build and run in detached mode
docker compose -f docker/docker-compose.yml -f docker/docker-compose.prod.yml up -d --build

# 3. Verify health
curl -s http://localhost:8000/api/health
```

---

## 🛡️ Production Verification Checklist

After deploying to any cloud provider, verify all 11 health criteria:
1. `GET /api/health` returns `{"status": "healthy", "model_loaded": true, "model_version": "v1.0.0"}`.
2. `GET /api/health/db-check` returns `{"status": "database connected"}`.
3. Employee login with `ADMIN_EMAIL` and `ADMIN_PASSWORD` returns a signed JWT.
4. `GET /api/workspace/me` validates organization and role (`admin`).
5. `GET /api/workspace/metrics` loads live KPI totals and revenue-at-risk.
6. `GET /api/workspace/risk-queue` returns prioritized customers sorted by `priority_score`.
7. `POST /api/workspace/customers/{id}/score` executes inference with `model_pipeline.pkl`.
8. SHAP explanation endpoint returns feature attributions without runtime errors.
9. Deterministic retention playbook engine returns valid action recommendations.
10. Multi-tenant checks reject requests without valid organization membership.
11. Security headers (`nosniff`, `DENY`, `no-store`) are returned on all API responses.
