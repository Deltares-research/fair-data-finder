import os
from contextlib import asynccontextmanager

from authlib.jose import OctKey
from api.core.stacdms import StacDmsApi
from api.extensions.core.sso_auth_extension import COOKIE_NAME, SSOAuthExtension
from api.extensions.keywords.keyword_client import KeywordClient
from api.extensions.rbac.rbac_client import RBACClient
from api.extensions.rbac.rbac_extension import RBACExtension
from api.schemas.requests import GroupGlobalRoleRequest
from fastapi import FastAPI
from fastapi_sso import MicrosoftSSO, OpenID
from sqlmodel import SQLModel, Session

import pytest
import pytest_asyncio
from api.config import APISettings
from api.database.db import create_db_engine, get_session
from api.database.models import (  # type: ignore
    Facility,
    FacilityKeywordGroupLink,
    Group,
    GroupCreate,
    Keyword_Group,
    Role,
    User,
)
from api.extensions.keywords.keyword_extension import KeywordExtension
from httpx import ASGITransport, AsyncClient
from stac_fastapi.api.models import create_get_request_model, create_post_request_model
from stac_fastapi.extensions.third_party import BulkTransactionExtension
from stac_fastapi.extensions.core import (
    FieldsExtension,
    SearchFilterExtension,
    SortExtension,
    TokenPaginationExtension,
    TransactionExtension,
)
from stac_fastapi.pgstac.core import CoreCrudClient
from stac_fastapi.pgstac.extensions.filter import FiltersClient
from stac_fastapi.pgstac.transactions import BulkTransactionsClient, TransactionsClient
from stac_fastapi.types.config import Settings

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


dms_settings = APISettings(
    azure_app_client_id="",
    azure_app_client_secret="",
    azure_tenant_id="",
    app_domain="",
    app_secret_key="",
    db_connection_url=f"sqlite:///{DATA_DIR}/test.db",
    environment="test",
)

Settings.set(dms_settings)

settings = Settings.get()


class _MockPgstacConnection:
    async def fetch(self, *_args, **_kwargs):
        return []


class _MockPgstacPool:
    @asynccontextmanager
    async def acquire(self):
        yield _MockPgstacConnection()


@pytest.fixture(scope="function")
def db_engine():
    db_engine = create_db_engine()
    SQLModel.metadata.drop_all(db_engine)
    SQLModel.metadata.create_all(db_engine)
    yield db_engine
    SQLModel.metadata.drop_all(db_engine)


@pytest.fixture(scope="function")
def keyword_client(db_engine):
    return KeywordExtension(db_engine=db_engine).client


@pytest_asyncio.fixture(scope="function")
async def app(db_engine):
    settings = Settings.get()
    filter_client = FiltersClient()
    search_filter_extension = SearchFilterExtension(client=filter_client)
    search_filter_extension.conformance_classes.append(
        "http://www.opengis.net/spec/cql2/1.0/conf/advanced-comparison-operators"
    )
    extensions = [
        TransactionExtension(
            client=TransactionsClient(),
            settings=settings,
        ),
        BulkTransactionExtension(client=BulkTransactionsClient()),
        FieldsExtension(),
        SortExtension(),
        TokenPaginationExtension(),
        search_filter_extension,
        KeywordExtension(db_engine=db_engine),
        SSOAuthExtension(
            settings=settings,
            sso_client=MicrosoftSSO(
                client_id=settings.azure_app_client_id,
                client_secret=settings.azure_app_client_secret,
            ),
        ),
        RBACExtension(),
    ]
    # SQLModel.metadata.create_all(db_engine)

    middlewares = []
    post_request_model = create_post_request_model(extensions)
    stac_dms_api = StacDmsApi(
        settings=settings,
        client=CoreCrudClient(pgstac_search_model=post_request_model),
        extensions=extensions,
        middlewares=middlewares,
        search_get_request_model=create_get_request_model(extensions),
        search_post_request_model=post_request_model,
    )
    # Unit tests use sqlite for RBAC/keyword data and do not spin up pgstac.
    # Provide lightweight pools so extensions using app.state.readpool don't fail.
    mock_pool = _MockPgstacPool()
    stac_dms_api.app.state.readpool = mock_pool
    stac_dms_api.app.state.writepool = mock_pool
    yield stac_dms_api.app


@pytest_asyncio.fixture(scope="function")
async def app_client(app: FastAPI):
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test-server"
    ) as c:
        yield c


@pytest.fixture(scope="function")
def db_session():
    return next(get_session())


@pytest.fixture(scope="function")
def rbac_client():
    return RBACExtension().client


@pytest_asyncio.fixture(scope="function")
async def keyword_group(keyword_client: KeywordClient):
    keyword_group = keyword_client.create_keywordgroup(
        {"group_name_nl": "test", "group_name_en": "engelse_test", "facility_type": "facility_type"}
    )
    yield keyword_group
    try:
        keyword_client.delete_keyword_group(str(keyword_group.id))
    except Exception:
        pass


@pytest_asyncio.fixture(scope="function")
async def facility(keyword_client: KeywordClient):
    facility = keyword_client.create_facility({"name": "test_facility"})
    yield facility
    try:
        keyword_client.delete_facility(str(facility.id))
    except Exception:
        pass


@pytest_asyncio.fixture(scope="function")
async def facility_keyword_group_link(
    keyword_client: KeywordClient, facility: Facility, keyword_group: Keyword_Group
):
    link = FacilityKeywordGroupLink(
        facility_id=str(facility.id), keyword_group_id=str(keyword_group.id)
    )
    _ = keyword_client.link_keywordgroup_to_facility(link)
    yield link
    try:
        keyword_client.unlink_keywordgroup_from_facility(link)
    except Exception:
        pass


@pytest_asyncio.fixture(scope="function")
async def keyword(keyword_client: KeywordClient, keyword_group: Keyword_Group):
    return keyword_client.create_keyword(
        {
            "group_id": keyword_group.id,
            "nl_keyword": "testwoord",
            "en_keyword": "english_testword",
        }
    )


@pytest_asyncio.fixture(scope="function")
async def filled_db(keyword_client: KeywordClient):
    # create facilities
    facility1 = keyword_client.create_facility({"name": "test_facility"})
    facility2 = keyword_client.create_facility({"name": "test_facility2"})

    # create keyword group
    keyword_group1 = keyword_client.create_keywordgroup(
        {"group_name_nl": "testgroup1", "group_name_en": "engelse_testgroup1", "facility_type": "facility_type1"}
    )
    keyword_group2 = keyword_client.create_keywordgroup(
        {"group_name_nl": "testgroup2", "group_name_en": "engelse_testgroup2", "facility_type": "facility_type2"}
    )

    # link facility1 to both keyword groups, facility2 to the second keyword group
    keyword_client.link_keywordgroup_to_facility(
        FacilityKeywordGroupLink(
            facility_id=str(facility1.id), keyword_group_id=str(keyword_group1.id)
        )
    )
    keyword_client.link_keywordgroup_to_facility(
        FacilityKeywordGroupLink(
            facility_id=str(facility1.id), keyword_group_id=str(keyword_group2.id)
        )
    )
    keyword_client.link_keywordgroup_to_facility(
        FacilityKeywordGroupLink(
            facility_id=str(facility2.id), keyword_group_id=str(keyword_group2.id)
        )
    )

    # fill keywordgroups with keywords
    keyword_client.create_keyword(
        {
            "group_id": keyword_group1.id,
            "nl_keyword": "testwoord1group1",
            "en_keyword": "english_testword",
        }
    )
    keyword_client.create_keyword(
        {
            "group_id": keyword_group1.id,
            "nl_keyword": "testwoord2group1",
            "en_keyword": "english_testword",
        }
    )
    keyword_client.create_keyword(
        {
            "group_id": keyword_group2.id,
            "nl_keyword": "testwoord1group2",
            "en_keyword": "english_testword",
        }
    )
    keyword_client.create_keyword(
        {
            "group_id": keyword_group2.id,
            "nl_keyword": "testwoord2group2",
            "en_keyword": "english_testword",
        }
    )
    return [facility1, facility2], [keyword_group1, keyword_group2]


@pytest_asyncio.fixture(scope="function")
async def user(rbac_client: RBACClient, db_session: Session):
    user = rbac_client.create_user(
        {
            "username": "test_user",
            "email": "test.test@deltares.nl",
        },
        db_session,
    )
    yield user
    try:
        rbac_client.delete_user(str(user.id))
    except Exception:
        pass


@pytest_asyncio.fixture(scope="function")
async def group(rbac_client: RBACClient, db_session: Session, user: User):
    group = rbac_client.create_group(
        {
            "name": "test_group",
            "description": "test_description",
        },
        db_session,
    )
    yield group
    try:
        rbac_client.delete_group(str(group.id))
    except Exception:
        pass


@pytest_asyncio.fixture(scope="function")
async def group_with_user(rbac_client: RBACClient, db_session: Session, user: User):
    group = rbac_client.create_group(
        {
            "name": "test_group",
            "description": "test_description",
        },
        db_session,
    )
    rbac_client.add_users_to_group(group.id, [user.email], db_session)
    yield group
    try:
        rbac_client.delete_group(str(group.id))
    except Exception:
        pass


@pytest_asyncio.fixture(scope="function")
async def data_producer_group(rbac_client: RBACClient, db_session: Session):
    group = rbac_client.create_group(
        GroupCreate(
            name="data_producer_group",
            description="data_producer_group",
        ),
        db_session,
    )
    rbac_client.assign_group_global_role(
        GroupGlobalRoleRequest(
            group_id=group.id,
            role=Role.DATA_PRODUCER,
        ),
        db_session,
    )
    yield group
    try:
        rbac_client.delete_group(str(group.id))
    except Exception:
        pass


@pytest_asyncio.fixture(scope="function")
async def keyword_editor_group(rbac_client: RBACClient, db_session: Session):
    group = rbac_client.create_group(
        GroupCreate(
            name="keyword_editor_group",
            description="keyword_editor_group",
        ),
        db_session,
    )
    rbac_client.assign_group_global_role(
        GroupGlobalRoleRequest(
            group_id=group.id,
            role=Role.KEYWORD_EDITOR,
        ),
        db_session,
    )
    yield group
    try:
        rbac_client.delete_group(str(group.id))
    except Exception:
        pass


@pytest_asyncio.fixture(scope="function")
async def admin_group(rbac_client: RBACClient, db_session: Session):
    group = rbac_client.create_group(
        GroupCreate(
            name="admin_group",
            description="admin_group",
        ),
        db_session,
    )
    rbac_client.assign_group_global_role(
        GroupGlobalRoleRequest(
            group_id=group.id,
            role=Role.ADMIN,
        ),
        db_session,
    )
    yield group
    try:
        rbac_client.delete_group(str(group.id))
    except Exception:
        pass


@pytest_asyncio.fixture(scope="function")
async def data_producer_user(
    rbac_client: RBACClient, data_producer_group: Group, db_session: Session
):
    user = rbac_client.create_user(
        {
            "username": "data_producer_user",
            "email": "data_producer_user@deltares.nl",
        },
        db_session,
    )
    rbac_client.add_users_to_group(data_producer_group.id, [user.email], db_session)
    yield user
    try:
        rbac_client.delete_user(str(user.id))
    except Exception:
        pass


@pytest_asyncio.fixture(scope="function")
async def keyword_editor_user(
    rbac_client: RBACClient, keyword_editor_group: Group, db_session: Session
):
    user = rbac_client.create_user(
        {
            "username": "keyword_editor_user",
            "email": "keyword_editor_user@deltares.nl",
        },
        db_session,
    )
    rbac_client.add_users_to_group(keyword_editor_group.id, [user.email], db_session)
    yield user
    try:
        rbac_client.delete_user(str(user.id))
    except Exception:
        pass


@pytest_asyncio.fixture(scope="function")
async def admin_user(rbac_client: RBACClient, admin_group: Group, db_session: Session):
    user = rbac_client.create_user(
        {
            "username": "admin_user",
            "email": "admin_user@deltares.nl",
        },
        db_session,
    )
    rbac_client.add_users_to_group(admin_group.id, [user.email], db_session)
    yield user
    try:
        rbac_client.delete_user(str(user.id))
    except Exception:
        pass


def _token(user: User):
    """Create a test JWT token for the given user."""
    user_openid = OpenID(
        email=user.email,
        name=user.username,
    )
    date, token = SSOAuthExtension.create_token(
        user_openid, OctKey.import_key(settings.app_secret_key)
    )
    return token


@pytest_asyncio.fixture(scope="function")
async def authenticated_client(app: FastAPI, user: User):
    token = _token(user)
    headers = {"Cookie": f"{COOKIE_NAME}={token}"}
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test-server", headers=headers
    ) as c:
        yield c


@pytest_asyncio.fixture(scope="function")
async def data_producer_client(app: FastAPI, data_producer_user: User):
    token = _token(data_producer_user)
    headers = {"Cookie": f"{COOKIE_NAME}={token}"}
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test-server", headers=headers
    ) as c:
        yield c


@pytest_asyncio.fixture(scope="function")
async def keyword_editor_client(app: FastAPI, keyword_editor_user: User):
    token = _token(keyword_editor_user)
    headers = {"Cookie": f"{COOKIE_NAME}={token}"}
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test-server", headers=headers
    ) as c:
        yield c


@pytest_asyncio.fixture(scope="function")
async def admin_client(app: FastAPI, admin_user: User):
    token = _token(admin_user)
    headers = {"Cookie": f"{COOKIE_NAME}={token}"}
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test-server", headers=headers
    ) as c:
        yield c
