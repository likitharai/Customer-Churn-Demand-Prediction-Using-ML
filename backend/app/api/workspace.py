import hashlib, io, json, secrets
from datetime import datetime, timedelta
import pandas as pd
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy import func
from app.core.tenancy import audit, require_manager, require_org_admin, tenant_context
from app.database.interaction_model import TenantInteraction
from app.database.model import Customer, User
from app.database.saas_models import AuditLog, DataImport, Invitation, Membership, ModelVersion, OrganizationCustomer, PredictionRecord, RetentionOutcome, RetentionPlaybook, RetentionTask
from app.services.prediction_service import PredictionService
from app.services.operational_risk import effective_probability, risk_level
from app.services.business_rules import priority_score, revenue_at_risk

router=APIRouter(); predictor=PredictionService()
class TaskInput(BaseModel):
    customer_id:str|None=None; assigned_user_id:int|None=None; title:str=Field(min_length=2,max_length=180); description:str|None=None; priority:str="medium"; due_at:datetime|None=None
class InteractionInput(BaseModel):
    customer_id:str|None=None; channel:str; subject:str=Field(min_length=2,max_length=160); notes:str|None=None; sentiment:str="neutral"; status:str="open"; follow_up_at:datetime|None=None
class OutcomeInput(BaseModel): customer_id:str; outcome:str; revenue_protected:float=0; notes:str|None=None
class PlaybookInput(BaseModel): name:str; description:str|None=None; trigger_risk:str="High"; recommended_action:str
class InviteInput(BaseModel): email:str; role:str=Field(pattern="^(agent|manager|admin)$")
class AssignmentInput(BaseModel): assigned_user_id:int|None=None
def oid(ctx): return ctx["organization"].id
def serialize(row): return {c.name:getattr(row,c.name) for c in row.__table__.columns}

@router.get("/me")
def me(ctx=Depends(tenant_context)): return {"organization":{"id":oid(ctx),"name":ctx["organization"].name,"plan":ctx["organization"].plan},"role":ctx["membership"].role}

@router.get("/metrics")
def metrics(ctx=Depends(tenant_context)):
    db,o=ctx["db"],oid(ctx); customers=db.query(OrganizationCustomer).filter_by(organization_id=o).count(); high=db.query(PredictionRecord).filter(PredictionRecord.organization_id==o,PredictionRecord.risk_level.in_(["High","Very High"])).count(); revenue=db.query(func.sum(PredictionRecord.revenue_at_risk)).filter_by(organization_id=o).scalar() or 0; tasks=db.query(RetentionTask).filter(RetentionTask.organization_id==o,RetentionTask.status!="completed").count(); protected=db.query(func.sum(RetentionOutcome.revenue_protected)).filter_by(organization_id=o).scalar() or 0; retained=db.query(RetentionOutcome).filter_by(organization_id=o,outcome="retained").count(); outcomes=db.query(RetentionOutcome).filter_by(organization_id=o).count()
    return {"customers":customers,"high_risk":high,"revenue_at_risk":round(float(revenue),2),"open_tasks":tasks,"revenue_protected":round(float(protected),2),"retention_success_rate":round(retained/outcomes*100,1) if outcomes else 0}

@router.get("/risk-queue")
def risk_queue(ctx=Depends(tenant_context)):
    db,o=ctx["db"],oid(ctx); result=[]
    for link,c in db.query(OrganizationCustomer,Customer).join(Customer,Customer.customer_id==OrganizationCustomer.customer_id).filter(OrganizationCustomer.organization_id==o).all():
        p=db.query(PredictionRecord).filter_by(organization_id=o,customer_id=c.customer_id).order_by(PredictionRecord.predicted_at.desc()).first(); probability=p.probability if p else 0
        result.append({"customer_id":c.customer_id,"monthly_charges":c.monthly_charges or 0,"contract":c.contract,"assigned_user_id":link.assigned_user_id,"risk_level":p.risk_level if p else "Unscored","probability":probability,"revenue_at_risk":p.revenue_at_risk if p else 0,"priority_score":round(priority_score(float(c.monthly_charges or 0), probability),2)})
    return sorted(result,key=lambda x:x["priority_score"],reverse=True)

@router.get("/customers/{customer_id}")
def profile(customer_id:str,ctx=Depends(tenant_context)):
    db,o=ctx["db"],oid(ctx); link=db.query(OrganizationCustomer).filter_by(organization_id=o,customer_id=customer_id).first()
    if not link: raise HTTPException(404,"Customer not found in this workspace")
    c=db.get(Customer,customer_id)
    predictions=[serialize(x) for x in db.query(PredictionRecord).filter_by(organization_id=o,customer_id=customer_id).order_by(PredictionRecord.predicted_at.desc()).limit(20)]
    ml_probability=float(predictions[0]["probability"] if predictions else 0)
    probability,source=effective_probability(db,o,customer_id,ml_probability)
    return {"customer":serialize(c),"assignment":serialize(link),"predictions":predictions,"current_risk":{"probability":probability,"ml_probability":ml_probability,"risk_level":risk_level(probability) if predictions else "Unscored","source":source},"interactions":[serialize(x) for x in db.query(TenantInteraction).filter_by(organization_id=o,customer_id=customer_id).order_by(TenantInteraction.created_at.desc())],"tasks":[serialize(x) for x in db.query(RetentionTask).filter_by(organization_id=o,customer_id=customer_id).order_by(RetentionTask.created_at.desc())],"outcomes":[serialize(x) for x in db.query(RetentionOutcome).filter_by(organization_id=o,customer_id=customer_id).order_by(RetentionOutcome.recorded_at.desc())]}

@router.post("/customers/{customer_id}/score")
def score(customer_id:str,ctx=Depends(tenant_context)):
    db,o,user=ctx["db"],oid(ctx),ctx["user"]
    if not db.query(OrganizationCustomer).filter_by(organization_id=o,customer_id=customer_id).first(): raise HTTPException(404,"Customer not found")
    c=db.get(Customer,customer_id); data={"gender":c.gender,"SeniorCitizen":c.senior_citizen or 0,"Partner":c.partner,"Dependents":c.dependents,"tenure":c.tenure or 0,"PhoneService":c.phone_service,"MultipleLines":c.multiple_lines,"InternetService":c.internet_service,"OnlineSecurity":c.online_security,"OnlineBackup":c.online_backup,"DeviceProtection":c.device_protection,"TechSupport":c.tech_support,"StreamingTV":c.streaming_tv,"StreamingMovies":c.streaming_movies,"Contract":c.contract,"PaperlessBilling":c.paperless_billing,"PaymentMethod":c.payment_method,"MonthlyCharges":c.monthly_charges or 0,"TotalCharges":c.total_charges or 0}
    try: result=predictor.predict(data)
    except Exception as exc: raise HTTPException(422,f"Customer cannot be scored: {exc}") from exc
    row=PredictionRecord(organization_id=o,customer_id=customer_id,created_by=user.id,probability=result["probability"],risk_level=result["risk_level"],prediction_label=result["prediction_label"],revenue_at_risk=round(revenue_at_risk(float(c.monthly_charges or 0), result["probability"]),2),model_version=predictor.predictor.metadata["model_version"],explanation_json=json.dumps({"input_snapshot":data}));db.add(row);audit(db,user,o,"prediction.created","customer",customer_id,result);db.commit();db.refresh(row);return serialize(row)

@router.put("/customers/{customer_id}/assignment")
def assign(customer_id:str,payload:AssignmentInput,ctx=Depends(require_manager)):
    row=ctx["db"].query(OrganizationCustomer).filter_by(organization_id=oid(ctx),customer_id=customer_id).first()
    if not row: raise HTTPException(404,"Customer not found")
    row.assigned_user_id=payload.assigned_user_id;audit(ctx["db"],ctx["user"],oid(ctx),"customer.assigned","customer",customer_id);ctx["db"].commit();return {"ok":True}

@router.get("/tasks")
def tasks(ctx=Depends(tenant_context)):
    q=ctx["db"].query(RetentionTask).filter_by(organization_id=oid(ctx));
    if ctx["membership"].role=="agent": q=q.filter((RetentionTask.assigned_user_id==ctx["user"].id)|(RetentionTask.assigned_user_id.is_(None)))
    return [serialize(x) for x in q.order_by(RetentionTask.due_at.asc())]
@router.post("/tasks",status_code=201)
def task(payload:TaskInput,ctx=Depends(tenant_context)):
    row=RetentionTask(organization_id=oid(ctx),created_by=ctx["user"].id,**payload.model_dump());ctx["db"].add(row);audit(ctx["db"],ctx["user"],oid(ctx),"task.created","task");ctx["db"].commit();ctx["db"].refresh(row);return serialize(row)
@router.patch("/tasks/{task_id}/complete")
def complete(task_id:int,ctx=Depends(tenant_context)):
    row=ctx["db"].query(RetentionTask).filter_by(id=task_id,organization_id=oid(ctx)).first()
    if not row: raise HTTPException(404,"Task not found")
    row.status="completed";row.completed_at=datetime.utcnow();audit(ctx["db"],ctx["user"],oid(ctx),"task.completed","task",task_id);ctx["db"].commit();return serialize(row)

@router.get("/interactions")
def interactions(ctx=Depends(tenant_context)): return [serialize(x) for x in ctx["db"].query(TenantInteraction).filter_by(organization_id=oid(ctx)).order_by(TenantInteraction.created_at.desc()).limit(500)]
@router.post("/interactions",status_code=201)
def interaction(payload:InteractionInput,ctx=Depends(tenant_context)):
    row=TenantInteraction(organization_id=oid(ctx),user_id=ctx["user"].id,**payload.model_dump());ctx["db"].add(row);audit(ctx["db"],ctx["user"],oid(ctx),"interaction.created","interaction");ctx["db"].commit();ctx["db"].refresh(row);return serialize(row)
@router.post("/outcomes",status_code=201)
def outcome(payload:OutcomeInput,ctx=Depends(tenant_context)):
    row=RetentionOutcome(organization_id=oid(ctx),recorded_by=ctx["user"].id,**payload.model_dump());ctx["db"].add(row);audit(ctx["db"],ctx["user"],oid(ctx),"outcome.recorded","customer",payload.customer_id);ctx["db"].commit();ctx["db"].refresh(row);return serialize(row)

@router.get("/playbooks")
def playbooks(ctx=Depends(tenant_context)): return [serialize(x) for x in ctx["db"].query(RetentionPlaybook).filter_by(organization_id=oid(ctx),is_active=True)]
@router.post("/playbooks",status_code=201)
def playbook(payload:PlaybookInput,ctx=Depends(require_manager)):
    row=RetentionPlaybook(organization_id=oid(ctx),**payload.model_dump());ctx["db"].add(row);audit(ctx["db"],ctx["user"],oid(ctx),"playbook.created","playbook");ctx["db"].commit();ctx["db"].refresh(row);return serialize(row)

@router.post("/imports/customers",status_code=201)
async def import_customers(file:UploadFile=File(...),ctx=Depends(require_manager)):
    if not file.filename.lower().endswith(".csv"): raise HTTPException(400,"Only CSV files are supported")
    db,o,user=ctx["db"],oid(ctx),ctx["user"]
    try: frame=pd.read_csv(io.BytesIO(await file.read()))
    except Exception as exc: raise HTTPException(400,f"Invalid CSV: {exc}") from exc
    count=0; mapping={"gender":"gender","SeniorCitizen":"senior_citizen","tenure":"tenure","MonthlyCharges":"monthly_charges","TotalCharges":"total_charges","Contract":"contract","Churn":"churn","Partner":"partner","Dependents":"dependents","PhoneService":"phone_service","MultipleLines":"multiple_lines","InternetService":"internet_service","OnlineSecurity":"online_security","OnlineBackup":"online_backup","DeviceProtection":"device_protection","TechSupport":"tech_support","StreamingTV":"streaming_tv","StreamingMovies":"streaming_movies","PaperlessBilling":"paperless_billing","PaymentMethod":"payment_method"}
    for raw in frame.to_dict("records"):
        cid=str(raw.get("customerID") or raw.get("customer_id") or "").strip()
        if not cid: continue
        c=db.get(Customer,cid) or Customer(customer_id=cid)
        for source,target in mapping.items():
            value=raw.get(source,raw.get(target));
            if pd.notna(value): setattr(c,target,value)
        db.add(c);db.flush()
        if not db.query(OrganizationCustomer).filter_by(organization_id=o,customer_id=cid).first(): db.add(OrganizationCustomer(organization_id=o,customer_id=cid,assigned_user_id=user.id))
        count+=1
    record=DataImport(organization_id=o,uploaded_by=user.id,filename=file.filename,row_count=count);db.add(record);audit(db,user,o,"customers.imported","data_import",details={"rows":count});db.commit();return {"import_id":record.id,"rows_imported":count}
@router.get("/imports")
def imports(ctx=Depends(require_manager)): return [serialize(x) for x in ctx["db"].query(DataImport).filter_by(organization_id=oid(ctx)).order_by(DataImport.created_at.desc())]

@router.post("/invitations",status_code=201)
def invite(payload:InviteInput,ctx=Depends(require_org_admin)):
    token=secrets.token_urlsafe(32);row=Invitation(organization_id=oid(ctx),email=payload.email.lower(),role=payload.role,token_hash=hashlib.sha256(token.encode()).hexdigest(),invited_by=ctx["user"].id,expires_at=datetime.utcnow()+timedelta(days=7));ctx["db"].add(row);audit(ctx["db"],ctx["user"],oid(ctx),"invitation.created","invitation",details={"email":payload.email,"role":payload.role});ctx["db"].commit();return {"invitation_id":row.id,"token":token,"expires_at":row.expires_at}
@router.post("/invitations/{token}/accept")
def accept(token:str,ctx=Depends(tenant_context)):
    row=ctx["db"].query(Invitation).filter_by(token_hash=hashlib.sha256(token.encode()).hexdigest()).first()
    if not row or row.accepted_at or row.expires_at<datetime.utcnow(): raise HTTPException(400,"Invitation is invalid or expired")
    m=ctx["db"].query(Membership).filter_by(user_id=ctx["user"].id).first();m.organization_id=row.organization_id;m.role=row.role;ctx["user"].role=row.role;row.accepted_at=datetime.utcnow();ctx["db"].commit();return {"accepted":True}
@router.get("/members")
def members(ctx=Depends(require_manager)): return [{"id":u.id,"full_name":u.full_name,"email":u.email,"company":u.company,"role":m.role,"is_active":u.is_active} for m,u in ctx["db"].query(Membership,User).join(User,User.id==Membership.user_id).filter(Membership.organization_id==oid(ctx)).all()]
@router.get("/models")
def models(ctx=Depends(require_manager)): return [serialize(x) for x in ctx["db"].query(ModelVersion).order_by(ModelVersion.created_at.desc())]
@router.get("/audit")
def audits(ctx=Depends(require_org_admin)): return [serialize(x) for x in ctx["db"].query(AuditLog).filter_by(organization_id=oid(ctx)).order_by(AuditLog.created_at.desc()).limit(500)]

