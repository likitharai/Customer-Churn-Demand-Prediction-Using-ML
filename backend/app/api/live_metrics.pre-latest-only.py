from datetime import datetime
from fastapi import APIRouter,Depends
from app.core.tenancy import tenant_context
from app.database.saas_models import OrganizationCustomer,PredictionRecord,RetentionOutcome,RetentionTask
router=APIRouter()
@router.get("/metrics")
def metrics(ctx=Depends(tenant_context)):
    db,o,user,role=ctx["db"],ctx["organization"].id,ctx["user"],ctx["membership"].role
    links=db.query(OrganizationCustomer).filter_by(organization_id=o)
    if role=="agent":links=links.filter_by(assigned_user_id=user.id)
    links=links.all();ids=[x.customer_id for x in links]
    predictions=db.query(PredictionRecord).filter(PredictionRecord.organization_id==o,PredictionRecord.customer_id.in_(ids)).all() if ids else []
    tasks=db.query(RetentionTask).filter(RetentionTask.organization_id==o,RetentionTask.status!="completed")
    if role=="agent":tasks=tasks.filter((RetentionTask.assigned_user_id==user.id)|(RetentionTask.assigned_user_id.is_(None)))
    outcomes=db.query(RetentionOutcome).filter(RetentionOutcome.organization_id==o,RetentionOutcome.customer_id.in_(ids)).all() if ids else [];retained=sum(x.outcome=="retained" for x in outcomes)
    return {"scope":"assigned" if role=="agent" else "organization","customers":len(links),"high_risk":sum(x.risk_level in {"High","Very High"} for x in predictions),"revenue_at_risk":round(sum(x.revenue_at_risk for x in predictions),2),"open_tasks":tasks.count(),"revenue_protected":round(sum(x.revenue_protected for x in outcomes),2),"retention_success_rate":round(retained/len(outcomes)*100,1) if outcomes else 0,"refreshed_at":datetime.utcnow().isoformat()}
