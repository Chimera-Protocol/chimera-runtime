"""Dashboard configuration."""

from __future__ import annotations

import os
from dataclasses import dataclass, field


@dataclass
class DashboardConfig:
    """Configuration for the Chimera Runtime Dashboard."""

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    # Paths — relative to chimera-runtime project root
    audit_dir: str = "./audit_logs"
    policies_dir: str = "./policies"
    config_path: str = "./.chimera/config.yaml"
    docs_output_dir: str = "./docs"

    # Auth
    secret_key: str = "chimera-dashboard-dev-secret-change-in-production"
    access_token_expire_minutes: int = 60 * 24  # 24 hours

    # Database
    database_url: str = "sqlite:///./data/chimera_dashboard.db"

    # Storage backend ("local" or "s3")
    storage_backend: str = "local"
    s3_bucket: str = ""
    s3_region: str = "us-east-1"

    # CORS
    cors_origins: list = field(default_factory=lambda: [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
    ])

    @classmethod
    def from_env(cls) -> "DashboardConfig":
        """Load config from environment variables."""
        cors_env = os.getenv("CHIMERA_CORS_ORIGINS", "")
        cors_origins = (
            [o.strip() for o in cors_env.split(",") if o.strip()]
            if cors_env
            else ["http://localhost:3000", "http://localhost:3001", "http://127.0.0.1:3000"]
        )
        return cls(
            host=os.getenv("CHIMERA_DASHBOARD_HOST", "0.0.0.0"),
            port=int(os.getenv("CHIMERA_DASHBOARD_PORT", "8000")),
            audit_dir=os.getenv("CHIMERA_AUDIT_DIR", "./audit_logs"),
            policies_dir=os.getenv("CHIMERA_POLICIES_DIR", "./policies"),
            config_path=os.getenv("CHIMERA_CONFIG_PATH", "./.chimera/config.yaml"),
            secret_key=os.getenv(
                "CHIMERA_SECRET_KEY",
                "chimera-dashboard-dev-secret-change-in-production",
            ),
            database_url=os.getenv(
                "CHIMERA_DATABASE_URL",
                "sqlite:///./data/chimera_dashboard.db",
            ),
            storage_backend=os.getenv("CHIMERA_STORAGE_BACKEND", "local"),
            s3_bucket=os.getenv("CHIMERA_S3_BUCKET", ""),
            s3_region=os.getenv("AWS_REGION", "us-east-1"),
            cors_origins=cors_origins,
        )
