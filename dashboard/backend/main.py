"""
Chimera Runtime Dashboard — FastAPI Backend

Usage:
    cd chimera-runtime
    uvicorn dashboard.backend.main:app --reload --port 8000

The backend directly imports chimera_runtime modules — zero adapter layer.
All audit data comes from the existing JSON file-based storage in audit_logs/.
"""

from __future__ import annotations

import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from .config import DashboardConfig
from .routers import audit, policies, analytics, compliance, auth, docs, settings, agents, leads, license, ingest, wallet, demo
from .models.user import create_tables
from .models.api_key import create_api_keys_table
from .models.wallet import create_wallet_tables
from .middleware.auth import init_auth_middleware
from .services.storage_service import create_storage_backend


# Ensure the project root is on sys.path so chimera_runtime is importable
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ============================================================================
# APP LIFESPAN
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize services on startup, cleanup on shutdown."""
    config = DashboardConfig.from_env()

    # Resolve paths relative to project root
    audit_dir = str(PROJECT_ROOT / config.audit_dir)
    policies_dir = str(PROJECT_ROOT / config.policies_dir)
    config_path = str(PROJECT_ROOT / config.config_path)

    # Initialize storage backend (S3 or local)
    storage = create_storage_backend(
        config.storage_backend,
        s3_bucket=config.s3_bucket,
        s3_region=config.s3_region,
        base_dir=audit_dir,
    )

    # Initialize all services
    audit.init_service(audit_dir, storage)
    policies.init_service(policies_dir)
    analytics.init_service(audit_dir, storage)
    compliance.init_service(audit_dir, policies_dir, config_path)

    # Docs service — serves repo docs/ as blog
    docs_dir = str(PROJECT_ROOT / "docs")
    docs.init_service(docs_dir)

    # Auth system — SQLite user database
    db_path = str(PROJECT_ROOT / config.database_url.replace("sqlite:///", ""))
    create_tables(db_path)
    create_api_keys_table(db_path)
    create_wallet_tables(db_path)
    auth.init_service(db_path, config.secret_key, config.access_token_expire_minutes)
    init_auth_middleware(auth.get_service(), db_path=db_path)
    settings.init_service(db_path)
    agents.init_service(audit._service)
    leads.init_service(db_path)
    ingest.init_service(storage, db_path)
    wallet.init_service(db_path)
    demo.init_service(storage, db_path, policies_dir)

    print(f"  Dashboard backend started")
    print(f"  Storage:      {config.storage_backend}" + (f" (s3://{config.s3_bucket})" if config.storage_backend == "s3" else f" ({audit_dir})"))
    print(f"  Policies dir: {policies_dir}")
    print(f"  Auth DB:      {db_path}")
    print(f"  API docs:     http://localhost:{config.port}/docs")

    yield

    print("  Dashboard backend shutting down")


# ============================================================================
# APP FACTORY
# ============================================================================

app = FastAPI(
    title="Chimera Runtime Dashboard",
    description="Runtime monitoring dashboard for AI agent policy enforcement and audit",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# No-cache middleware — prevent browsers/proxies from caching API responses
class NoCacheMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
        return response

# CORS
config = DashboardConfig.from_env()
app.add_middleware(NoCacheMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routers
app.include_router(auth.router, prefix="/api/v1")
app.include_router(audit.router, prefix="/api/v1")
app.include_router(policies.router, prefix="/api/v1")
app.include_router(analytics.router, prefix="/api/v1")
app.include_router(compliance.router, prefix="/api/v1")
app.include_router(docs.router, prefix="/api/v1")
app.include_router(settings.router, prefix="/api/v1")
app.include_router(agents.router, prefix="/api/v1")
app.include_router(leads.router, prefix="/api/v1")
app.include_router(ingest.router, prefix="/api/v1")
app.include_router(wallet.router, prefix="/api/v1")
app.include_router(demo.router, prefix="/api/v1")
app.include_router(license.router)


# ============================================================================
# HEALTH CHECK
# ============================================================================

@app.get("/api/v1/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "ok",
        "service": "chimera-runtime-dashboard",
        "version": "1.0.0",
    }


# ============================================================================
# CLI RUNNER
# ============================================================================

def run():
    """Entry point for `chimera-dashboard` CLI command."""
    import uvicorn
    config = DashboardConfig.from_env()
    uvicorn.run(
        "dashboard.backend.main:app",
        host=config.host,
        port=config.port,
        reload=True,
    )


if __name__ == "__main__":
    run()
