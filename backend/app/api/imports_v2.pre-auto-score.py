import io

import pandas as pd
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from app.core.tenancy import audit, require_manager
from app.database.model import Customer
from app.database.saas_models import DataImport, OrganizationCustomer


router = APIRouter()


def normalize(value, target):
    text = str(value).strip()
    lower = text.lower()
    if target == "senior_citizen":
        return int(lower in {"1", "true", "yes"})
    if target == "tenure":
        return int(float(value))
    if target in {"monthly_charges", "total_charges"}:
        return float(value) if text else 0.0
    if lower in {"true", "false"} and target not in {"gender", "contract", "internet_service", "payment_method"}:
        return "Yes" if lower == "true" else "No"
    return value


@router.post("/imports/customers", status_code=201)
async def import_customers(file: UploadFile = File(...), context=Depends(require_manager)):
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(400, "Only CSV files are supported")
    try:
        content = await file.read()
        frame = pd.read_csv(io.BytesIO(content))
    except Exception as exc:
        raise HTTPException(400, f"Invalid CSV: {exc}") from exc
    if frame.empty:
        raise HTTPException(400, "The CSV file contains no customer rows")

    db = context["db"]
    organization_id = context["organization"].id
    user = context["user"]
    mapping = {
        "gender": "gender", "SeniorCitizen": "senior_citizen", "tenure": "tenure",
        "MonthlyCharges": "monthly_charges", "TotalCharges": "total_charges", "Contract": "contract",
        "Churn": "churn", "Partner": "partner", "Dependents": "dependents", "PhoneService": "phone_service",
        "MultipleLines": "multiple_lines", "InternetService": "internet_service", "OnlineSecurity": "online_security",
        "OnlineBackup": "online_backup", "DeviceProtection": "device_protection", "TechSupport": "tech_support",
        "StreamingTV": "streaming_tv", "StreamingMovies": "streaming_movies", "PaperlessBilling": "paperless_billing",
        "PaymentMethod": "payment_method",
    }
    count = 0
    try:
        for raw in frame.to_dict("records"):
            customer_id = str(raw.get("customerID") or raw.get("customer_id") or "").strip()
            if not customer_id:
                continue
            customer = db.get(Customer, customer_id) or Customer(customer_id=customer_id)
            for source, target in mapping.items():
                value = raw.get(source, raw.get(target))
                if pd.notna(value):
                    setattr(customer, target, normalize(value, target))
            db.add(customer)
            db.flush()
            link = db.query(OrganizationCustomer).filter_by(
                organization_id=organization_id, customer_id=customer_id
            ).first()
            if not link:
                db.add(OrganizationCustomer(
                    organization_id=organization_id,
                    customer_id=customer_id,
                    assigned_user_id=user.id,
                ))
            count += 1
        if not count:
            raise ValueError("No rows contained customerID or customer_id")
        record = DataImport(
            organization_id=organization_id,
            uploaded_by=user.id,
            filename=file.filename,
            row_count=count,
        )
        db.add(record)
        db.flush()
        audit(db, user, organization_id, "customers.imported", "data_import", record.id,
              {"filename": file.filename, "rows": count})
        db.commit()
        db.refresh(record)
        return {"import_id": record.id, "rows_imported": count}
    except Exception as exc:
        db.rollback()
        raise HTTPException(422, f"Import failed: {exc}") from exc


@router.delete("/imports/{import_id}")
def delete_import(import_id: int, context=Depends(require_manager)):
    db = context["db"]
    organization_id = context["organization"].id
    record = db.query(DataImport).filter_by(id=import_id, organization_id=organization_id).first()
    if not record:
        raise HTTPException(404, "CSV import record not found")
    filename = record.filename
    rows = record.row_count
    db.delete(record)
    audit(db, context["user"], organization_id, "data_import.deleted", "data_import", import_id,
          {"filename": filename, "rows": rows})
    db.commit()
    return {
        "deleted": True,
        "import_id": import_id,
        "message": f"Import record for {filename} was deleted. The source CSV was never stored on the server.",
    }
