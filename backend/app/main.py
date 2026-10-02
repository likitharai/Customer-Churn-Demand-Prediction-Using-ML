import os

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from app.api import auth_b2b, health, imports_v2, invitations_v2, live_metrics, prediction, retention_workflow, role_views, workspace
from app.core.config import is_production
from app.core.security import get_current_user
from app.core.startup import lifespan


app = FastAPI(
    title="RetainIQ API",
    description="Invitation-only B2B customer retention intelligence",
    version="3.4.0",
    lifespan=lifespan,
    docs_url=None if is_production() else "/docs",
    redoc_url=None if is_production() else "/redoc",
    openapi_url=None if is_production() else "/openapi.json",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store"
        return response


app.add_middleware(SecurityHeadersMiddleware)


app.include_router(health.router, prefix="/api/health", tags=["Health"])
app.include_router(auth_b2b.router, prefix="/api/auth", tags=["Employee authentication"])
app.include_router(imports_v2.router, prefix="/api/workspace", tags=["Customer imports"])
app.include_router(invitations_v2.router, prefix="/api/workspace", tags=["Employee invitations"])
app.include_router(live_metrics.router, prefix="/api/workspace", tags=["Dashboard"])
app.include_router(role_views.router, prefix="/api/workspace", tags=["Role dashboards"])
app.include_router(workspace.router, prefix="/api/workspace", tags=["Workspace operations"])
app.include_router(retention_workflow.router, prefix="/api/workspace", tags=["Connected retention workflow"])
app.include_router(prediction.router, prefix="/api/prediction", tags=["Ad hoc prediction"], dependencies=[Depends(get_current_user)])
 
# Static SPA Serving for All-in-One deployment
from pathlib import Path
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

FRONTEND_DIST = Path(__file__).resolve().parents[2] / "frontend" / "dist"
if not FRONTEND_DIST.exists():
    FRONTEND_DIST = Path("/app/frontend/dist")

if FRONTEND_DIST.exists() and (FRONTEND_DIST / "index.html").exists():
    if (FRONTEND_DIST / "assets").exists():
        app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIST / "assets")), name="assets")

    @app.get("/")
    async def serve_root():
        return FileResponse(FRONTEND_DIST / "index.html")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        if full_path.startswith("api/") or full_path == "api":
            return {"error": "API route not found"}
        file_path = FRONTEND_DIST / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(FRONTEND_DIST / "index.html")
else:
    @app.get("/")
    def root():
        return {"message": "RetainIQ B2B API is running", "version": "3.4.0"}

if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "8000"))
    host = os.getenv("HOST", "0.0.0.0")
    uvicorn.run("app.main:app", host=host, port=port, reload=False)



