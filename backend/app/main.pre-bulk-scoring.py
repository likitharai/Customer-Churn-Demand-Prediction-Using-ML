import os

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth_b2b, health, imports_v2, invitations_v2, live_metrics, prediction, role_views, workspace
from app.core.security import get_current_user
from app.core.startup import lifespan


app = FastAPI(
    title="RetainIQ API",
    description="Invitation-only B2B customer retention intelligence",
    version="3.2.0",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"message": "RetainIQ B2B API is running", "version": "3.2.0"}


app.include_router(health.router, prefix="/api/health", tags=["Health"])
app.include_router(auth_b2b.router, prefix="/api/auth", tags=["Employee authentication"])
app.include_router(imports_v2.router, prefix="/api/workspace", tags=["Customer imports"])
app.include_router(invitations_v2.router, prefix="/api/workspace", tags=["Employee invitations"])
app.include_router(live_metrics.router, prefix="/api/workspace", tags=["Dashboard"])
app.include_router(role_views.router, prefix="/api/workspace", tags=["Role dashboards"])
app.include_router(workspace.router, prefix="/api/workspace", tags=["Workspace operations"])
app.include_router(
    prediction.router,
    prefix="/api/prediction",
    tags=["Ad hoc prediction"],
    dependencies=[Depends(get_current_user)],
)
