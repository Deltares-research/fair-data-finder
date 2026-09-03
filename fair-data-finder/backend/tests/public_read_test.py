"""Tests for anonymous read access when public_read_enabled is set."""

from contextlib import asynccontextmanager

import pytest
import pytest_asyncio
from api.core.stacdms import StacDmsApi
from api.extensions.core.sso_auth_extension import (
    PUBLIC_READ_ENDPOINTS,
    SSOAuthExtension,
)
from api.extensions.keywords.keyword_extension import KeywordExtension
from api.extensions.rbac.rbac_extension import RBACExtension
from fastapi import FastAPI
from fastapi.routing import APIRoute
from fastapi_sso import MicrosoftSSO
from httpx import ASGITransport, AsyncClient
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
from stac_fastapi.pgstac.extensions.filter import FiltersClient
from stac_fastapi.pgstac.transactions import BulkTransactionsClient, TransactionsClient
from stac_fastapi.types.config import Settings


class _MockPgstacConnection:
    async def fetch(self, *_args, **_kwargs):
        return []


class _MockPgstacPool:
    @asynccontextmanager
    async def acquire(self):
        yield _MockPgstacConnection()


@pytest_asyncio.fixture(scope="function")
async def public_read_app(db_engine):
    """Build the API with the public read endpoints exposed."""
    async for app in _build_app(db_engine, login_enabled=True):
        yield app


@pytest_asyncio.fixture(scope="function")
async def no_login_app(db_engine):
    """Build the API with the login endpoints disabled (AUTH_ENABLED=false)."""
    async for app in _build_app(db_engine, login_enabled=False):
        yield app


async def _build_app(db_engine, login_enabled: bool):
    settings = Settings.get()
    filter_client = FiltersClient()
    search_filter_extension = SearchFilterExtension(client=filter_client)
    extensions = [
        TransactionExtension(client=TransactionsClient(), settings=settings),
        BulkTransactionExtension(client=BulkTransactionsClient()),
        FieldsExtension(),
        SortExtension(),
        TokenPaginationExtension(),
        search_filter_extension,
        KeywordExtension(db_engine=db_engine),
        RBACExtension(),
        SSOAuthExtension(
            settings=settings,
            sso_client=MicrosoftSSO(
                client_id=settings.azure_app_client_id,
                client_secret=settings.azure_app_client_secret,
            ),
            login_enabled=login_enabled,
            public_endpoints=PUBLIC_READ_ENDPOINTS,
        ),
    ]

    post_request_model = create_post_request_model(extensions)
    stac_dms_api = StacDmsApi(
        settings=settings,
        client=CoreCrudClient(pgstac_search_model=post_request_model),
        extensions=extensions,
        middlewares=[],
        search_get_request_model=create_get_request_model(extensions),
        search_post_request_model=post_request_model,
    )
    mock_pool = _MockPgstacPool()
    stac_dms_api.app.state.readpool = mock_pool
    stac_dms_api.app.state.writepool = mock_pool
    yield stac_dms_api.app


@pytest_asyncio.fixture(scope="function")
async def public_read_client(public_read_app: FastAPI):
    async with AsyncClient(
        transport=ASGITransport(app=public_read_app), base_url="http://test-server"
    ) as c:
        yield c


@pytest.mark.asyncio
async def test_public_read_endpoints_exist_on_the_app(public_read_app: FastAPI):
    """Every path in PUBLIC_READ_ENDPOINTS must match a registered route exactly."""
    registered = {
        (route.path, method)
        for route in public_read_app.routes
        if hasattr(route, "methods")
        for method in route.methods
    }
    missing = [
        endpoint
        for endpoint in PUBLIC_READ_ENDPOINTS
        if (endpoint["path"], endpoint["method"]) not in registered
    ]
    assert missing == []


def _requires_login(route: APIRoute) -> bool:
    """Whether the route has the SSO login dependency attached."""
    return any(
        dependency.call is SSOAuthExtension.get_logged_user
        for dependency in route.dependant.dependencies
    )


@pytest.mark.asyncio
async def test_public_read_endpoints_have_no_login_dependency(public_read_app: FastAPI):
    """No endpoint in PUBLIC_READ_ENDPOINTS may require the auth cookie."""
    public = {(e["path"], e["method"]) for e in PUBLIC_READ_ENDPOINTS}
    protected = [
        (route.path, method)
        for route in public_read_app.routes
        if isinstance(route, APIRoute) and _requires_login(route)
        for method in route.methods
        if (route.path, method) in public
    ]
    assert protected == []


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "path,method",
    [
        ("/collections", "POST"),
        ("/collections/{collection_id}", "PUT"),
        ("/collections/{collection_id}", "DELETE"),
        ("/collections/{collection_id}/items", "POST"),
        ("/collections/{collection_id}/items/{item_id}", "PUT"),
        ("/collections/{collection_id}/items/{item_id}", "DELETE"),
        ("/collections/{collection_id}/bulk_items", "POST"),
        ("/keyword", "POST"),
        ("/facility", "POST"),
        ("/keywordgroup", "POST"),
        ("/permissions", "GET"),
        ("/users", "GET"),
        ("/groups", "GET"),
    ],
)
async def test_write_and_rbac_endpoints_keep_login_dependency(
    public_read_app: FastAPI, path: str, method: str
):
    routes = [
        route
        for route in public_read_app.routes
        if isinstance(route, APIRoute) and route.path == path and method in route.methods
    ]
    assert routes, f"route {method} {path} is not registered"
    assert all(_requires_login(route) for route in routes)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "path",
    [
        "/conformance",
        "/keywords",
        "/keywordgroups",
        "/facilities",
        "/_mgmt/ping",
    ],
)
async def test_read_endpoints_are_public(public_read_client: AsyncClient, path: str):
    response = await public_read_client.get(path)
    assert response.status_code != 401


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "method,path",
    [
        ("POST", "/collections"),
        ("POST", "/collections/test-collection/items"),
        ("POST", "/keyword"),
        ("POST", "/facility"),
        ("POST", "/keywordgroup"),
    ],
)
async def test_write_endpoints_still_require_auth(
    public_read_client: AsyncClient, method: str, path: str
):
    response = await public_read_client.request(method, path, json={})
    assert response.status_code in (401, 403)


@pytest.mark.asyncio
async def test_rbac_endpoints_still_require_auth(public_read_client: AsyncClient):
    response = await public_read_client.get("/permissions")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_endpoints_absent_when_login_disabled(no_login_app: FastAPI):
    auth_paths = [
        route.path
        for route in no_login_app.routes
        if isinstance(route, APIRoute) and route.path.startswith("/auth")
    ]
    assert auth_paths == []


@pytest.mark.asyncio
async def test_disabling_login_does_not_widen_access(
    no_login_app: FastAPI, public_read_app: FastAPI
):
    """AUTH_ENABLED=false must never expose a route that was previously protected."""

    def open_routes(app: FastAPI) -> set:
        return {
            (route.path, method)
            for route in app.routes
            if isinstance(route, APIRoute) and not _requires_login(route)
            for method in route.methods
        }

    public = {(e["path"], e["method"]) for e in PUBLIC_READ_ENDPOINTS}
    public.add(("/", "GET"))
    assert open_routes(no_login_app) - public == set()
    assert open_routes(no_login_app) <= open_routes(public_read_app)
