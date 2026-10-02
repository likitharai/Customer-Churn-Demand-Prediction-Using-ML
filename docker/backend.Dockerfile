FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app/backend

COPY backend/requirements.txt .
RUN python -m pip install --upgrade pip && \
    pip install --no-cache-dir --timeout 180 --retries 10 --prefer-binary -r requirements.txt

COPY backend/ ./
COPY database/migrations/ /app/database/migrations/
COPY ml_pipeline/ /app/ml_pipeline/
COPY reports/ /app/reports/
COPY model_pipeline.pkl /app/model_pipeline.pkl

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]

