FROM python:3.10-slim

WORKDIR /app

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .
COPY ml_pipeline/ ./ml_pipeline
COPY reports/ ./reports
COPY model_pipeline.pkl ./model_pipeline.pkl

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]