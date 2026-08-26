"""FastAPI application."""

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi_sso.sso.microsoft import MicrosoftSSO
from stac_fastapi.api.models import create_get_request_model, create_post_request_model
from stac_fastapi.extensions.core import (
    FieldsExtension,
    SearchFilterExtension,
    SortExtension,
    TokenPaginationExtension,
    TransactionExtension,
)
from stac_fastapi.extensions.third_party import BulkTransactionExtension
from stac_fastapi.pgstac.core import CoreCrudClient
from stac_fastapi.pgstac.db import close_db_connection, connect_to_db
from stac_fastapi.pgstac.extensions.filter import FiltersClient
from stac_fastapi.pgstac.types.search import PgstacSearch
from stac_fastapi.pgstac.transactions import BulkTransactionsClient
from api.extensions.core.transactions_client import NullGeometryTransactionsClient
from stac_fastapi.types.config import Settings

from api.config import APISettings
from api.core.stacdms import StacDmsApi
from api.core.startup import create_admin_users, run_migrations
from api.database.db import create_db_engine
from api.extensions.core.sso_auth_extension import (
    PUBLIC_READ_ENDPOINTS,
    SSOAuthExtension,
)
from api.extensions.keywords.keyword_extension import KeywordExtension
from api.extensions.rbac.rbac_extension import RBACExtension


Settings.set(APISettings())
settings: APISettings = Settings.get()
_LOGGER = logging.getLogger("uvicorn.default")
db_engine = create_db_engine()

filter_client = FiltersClient()
search_filter_extension = SearchFilterExtension(client=filter_client)
search_filter_extension.conformance_classes.append(
    "http://www.opengis.net/spec/cql2/1.0/conf/advanced-comparison-operators"
)

extensions = [
    TransactionExtension(
        client=NullGeometryTransactionsClient(),
        settings=settings,
    ),
    BulkTransactionExtension(client=BulkTransactionsClient()),
    FieldsExtension(),
    SortExtension(),
    TokenPaginationExtension(),
    search_filter_extension,
    KeywordExtension(db_engine=db_engine),
]

extensions.append(RBACExtension())

# The SSO extension is always registered: it is what applies the authentication
# dependency to every non-public route. `auth_enabled` only controls whether the
# /auth/* login endpoints exist, so disabling it never widens access.
sso_client = MicrosoftSSO(
    client_id=settings.azure_app_client_id,
    client_secret=settings.azure_app_client_secret,
    tenant=settings.azure_tenant_id,
    redirect_uri=f"https://{settings.app_domain}/api/auth/callback",
    allow_insecure_http=True,
)
extensions.append(
    SSOAuthExtension(
        settings=settings,
        sso_client=sso_client,
        login_enabled=settings.auth_enabled,
        public_endpoints=(
            PUBLIC_READ_ENDPOINTS if settings.public_read_enabled else []
        ),
    )
)

middlewares = []

post_request_model = create_post_request_model(extensions, base_model=PgstacSearch)


@asynccontextmanager
async def lifespan(app: FastAPI):
    run_migrations()
    create_admin_users()
    await connect_to_db(app, add_write_connection_pool=True)
    yield
    await close_db_connection(app)


app = FastAPI(
    lifespan=lifespan,
    openapi_url=settings.openapi_url,
    docs_url=settings.docs_url,
    redoc_url=None,
)
app.root_path = os.getenv("STAC_FASTAPI_ROOT_PATH", "/api")

api = StacDmsApi(
    app=app,
    title=os.getenv("STAC_FASTAPI_TITLE", "stac-fastapi-pgstac"),
    description=os.getenv("STAC_FASTAPI_DESCRIPTION", "stac-fastapi-pgstac"),
    api_version=os.getenv("STAC_FASTAPI_VERSION", "2.1"),
    settings=settings,
    extensions=extensions,
    middlewares=middlewares,
    client=CoreCrudClient(pgstac_search_model=post_request_model),
    search_get_request_model=create_get_request_model(extensions),
    search_post_request_model=post_request_model,
)
