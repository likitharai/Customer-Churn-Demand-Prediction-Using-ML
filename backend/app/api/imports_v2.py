import io
import json

import pandas as pd
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from app.core.tenancy import audit, require_manager
from app.database.model import Customer
from app.database.saas_models import DataImport, OrganizationCustomer, PredictionRecord
from app.services.business_rules import revenue_at_risk
from app.services.prediction_service import PredictionService


router = APIRouter()
predictor = PredictionService()


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


def prediction_input(customer):
    return {
        "gender": customer.gender,
        "SeniorCitizen": customer.senior_citizen or 0,
        "Partner": customer.partner,
        "Dependents": customer.dependents,
        "tenure": customer.tenure or 0,
        "PhoneService": customer.phone_service,
        "MultipleLines": customer.multiple_lines,
        "InternetService": customer.internet_service,
        "OnlineSecurity": customer.online_security,
        "OnlineBackup": customer.online_backup,
        "DeviceProtection": customer.device_protection,
        "TechSupport": customer.tech_support,
        "StreamingTV": customer.streaming_tv,
        "StreamingMovies": customer.streaming_movies,
        "Contract": customer.contract,
        "PaperlessBilling": customer.paperless_billing,
        "PaymentMethod": customer.payment_method,
        "MonthlyCharges": customer.monthly_charges or 0,
        "TotalCharges": customer.total_charges or 0,
    }


def score_customer(db, organization_id, user_id, customer):
    features = prediction_input(customer)
    result = predictor.predict(features)
    db.add(PredictionRecord(
        organization_id=organization_id,
        customer_id=customer.customer_id,
        created_by=user_id,
        probability=result["probability"],
        risk_level=result["risk_level"],
        prediction_label=result["prediction_label"],
        revenue_at_risk=round(revenue_at_risk(float(customer.monthly_charges or 0), result["probability"]), 2),
        model_version=predictor.predictor.metadata["model_version"],
        explanation_json=json.dumps({"input_snapshot": features}),
    ))


def score_customers(db, organization_id, user_id, customers):
    scored = 0
    failures = []
    for customer in customers:
        try:
            score_customer(db, organization_id, user_id, customer)
            scored += 1
        except Exception as exc:
            failures.append({"customer_id": customer.customer_id, "error": str(exc)[:240]})
    return scored, failures


@router.post("/imports/customers", status_code=201)
async def import_customers(file: UploadFile = File(...), context=Depends(require_manager)):
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(400, "Only CSV files are supported")
    try:
        frame = pd.read_csv(io.BytesIO(await file.read()))
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
    imported = []
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
                    assigned_user_id=None,
                ))
            imported.append(customer)
        if not imported:
            raise ValueError("No rows contained customerID or customer_id")

        scored, failures = score_customers(db, organization_id, user.id, imported)
        record = DataImport(
            organization_id=organization_id,
            uploaded_by=user.id,
            filename=file.filename,
            row_count=len(imported),
            status="completed" if not failures else "completed_with_errors",
            error_message=json.dumps(failures[:20]) if failures else None,
        )
        db.add(record)
        db.flush()
        audit(db, user, organization_id, "customers.imported_and_scored", "data_import", record.id, {
            "filename": file.filename,
            "rows": len(imported),
            "predictions_created": scored,
            "scoring_errors": len(failures),
        })
        db.commit()
        return {
            "import_id": record.id,
            "rows_imported": len(imported),
            "predictions_created": scored,
            "scoring_errors": len(failures),
        }
    except Exception as exc:
        db.rollback()
        raise HTTPException(422, f"Import failed: {exc}") from exc


@router.post("/imports/score-all")
def score_all_customers(context=Depends(require_manager)):
    db = context["db"]
    organization_id = context["organization"].id
    user = context["user"]
    customers = [customer for customer, in (
        db.query(Customer)
        .join(OrganizationCustomer, OrganizationCustomer.customer_id == Customer.customer_id)
        .filter(OrganizationCustomer.organization_id == organization_id)
        .all()
    )]
    scored, failures = score_customers(db, organization_id, user.id, customers)
    audit(db, user, organization_id, "customers.bulk_scored", "organization", organization_id, {
        "predictions_created": scored,
        "scoring_errors": len(failures),
    })
    db.commit()
    return {"predictions_created": scored, "scoring_errors": len(failures), "errors": failures[:20]}


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
    return {"deleted": True, "import_id": import_id,
            "message": f"Import record for {filename} was deleted. The source CSV was never stored on the server."}
