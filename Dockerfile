# Multi-stage Docker build for RetainIQ Full-Stack Platform
# Stage 1: Build the React Frontend
FROM node:18-alpine AS frontend-builder
WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm install

COPY frontend/ ./
RUN npm run build

# Stage 2: Python Backend + ML Model + Embedded Frontend
FROM python:3.10-slim

# System dependencies (libgomp1 is required by LightGBM for OpenMP multiprocessing)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python backend dependencies
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy authoritative model artifact and reports
COPY model_pipeline.pkl ./
COPY reports/ ./reports/

# Copy backend application code
COPY backend/ ./backend/

# Copy compiled React frontend assets from stage 1
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Configure environment for Hugging Face Spaces / Container platforms (Default Port 7860)
ENV PORT=7860 \
    HOST=0.0.0.0 \
    APP_ENV=development \
    MODEL_PATH=/app/model_pipeline.pkl \
    PYTHONPATH=/app/backend:/app

EXPOSE 7860

# Run FastAPI serving both the React UI and API endpoints
CMD ["python", "-m", "uvicorn", "app.main:app", "--app-dir", "backend", "--host", "0.0.0.0", "--port", "7860"]
