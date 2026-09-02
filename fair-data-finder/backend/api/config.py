from typing import Optional

from stac_fastapi.pgstac.config import Settings as PgstacSettings


class APISettings(PgstacSettings):
    """API settings for the pgstac-backed deployment."""

    azure_app_client_id: str = ""
    azure_app_client_secret: str = ""
    azure_tenant_id: str = ""
    app_domain: str = ""
    app_secret_key: str = ""
    # Kept for Alembic/SQLModel (RBAC + Keywords tables)
    db_connection_url: str = ""
    environment: str = "local"
    frontend_url: str = ""
    admin_users: Optional[str] = None
    # Secure by default: a missing value must fail towards the safe behaviour.
    # Only set COOKIE_SECURE=false for local dev served over plain HTTP.
    cookie_secure: bool = True
