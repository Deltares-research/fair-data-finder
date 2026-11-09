import pytest
from api.core.dependencies import user_can_update_item, user_has_collection_permission
from api.database.models import (
    Group,
    GroupRole,
    GroupUserLink,
    ItemOwner,
    Permission,
    Role,
    User,
)
from api.extensions.core.sso_auth_extension import COOKIE_NAME
from api.extensions.core.transactions_client import (
    NullGeometryTransactionsClient,
    OwnerTrackingBulkTransactionsClient,
)
from api.extensions.rbac.rbac_client import RBACClient
from fastapi import FastAPI, HTTPException
from sqlmodel import Session, select
from stac_fastapi.extensions.third_party.bulk_transactions import (
    BulkTransactionMethod,
    Items,
)
from stac_fastapi.pgstac.transactions import BulkTransactionsClient, TransactionsClient
from stac_pydantic import Item, ItemCollection
from starlette.requests import Request

from tests.conftest import _token

COLLECTION_ID = "test-collection"


def _item_dict(item_id: str) -> dict:
    return {
        "type": "Feature",
        "stac_version": "1.0.0",
        "id": item_id,
        "geometry": None,
        "properties": {"datetime": "2020-01-01T00:00:00Z"},
        "links": [],
        "assets": {},
    }


def _request(user: User) -> Request:
    return Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/",
            "query_string": b"",
            "headers": [(b"cookie", f"{COOKIE_NAME}={_token(user)}".encode())],
            "path_params": {"collection_id": COLLECTION_ID},
        }
    )


def _owners(db_session: Session) -> dict[str, str]:
    db_session.expire_all()
    rows = db_session.exec(
        select(ItemOwner).where(ItemOwner.collection_id == COLLECTION_ID)
    ).all()
    return {row.item_id: row.owner_email for row in rows}


def _give_role(
    db_session: Session, user: User, role: Role, collection_id: str | None
) -> None:
    """Put the user in a new group with the role (collection_id None = whole app)."""
    group = Group(name=f"{role.value}-{collection_id}", description="test")
    db_session.add(group)
    db_session.commit()
    db_session.add(GroupUserLink(group_id=group.id, user_email=user.email))
    db_session.add(GroupRole(group_id=group.id, role=role, object=collection_id))
    db_session.commit()


def _set_owner(db_session: Session, item_id: str, owner_email: str) -> None:
    db_session.add(
        ItemOwner(collection_id=COLLECTION_ID, item_id=item_id, owner_email=owner_email)
    )
    db_session.commit()


@pytest.fixture(scope="function")
def no_pgstac(monkeypatch: pytest.MonkeyPatch) -> None:
    """Replace the pgSTAC writes; the tests only check the owner records."""

    async def _noop(*_args, **_kwargs):
        return None

    for client, method in [
        (TransactionsClient, "create_item"),
        (TransactionsClient, "delete_item"),
        (TransactionsClient, "delete_collection"),
        (BulkTransactionsClient, "bulk_item_insert"),
    ]:
        monkeypatch.setattr(client, method, _noop)


@pytest.mark.asyncio
async def test_create_item_records_owner(
    app: FastAPI, user: User, db_session: Session, no_pgstac: None
):
    client = NullGeometryTransactionsClient()

    await client.create_item(
        collection_id=COLLECTION_ID,
        item=Item(**_item_dict("item-1")),
        request=_request(user),
    )
    await client.create_item(
        collection_id=COLLECTION_ID,
        item=ItemCollection(
            type="FeatureCollection",
            features=[_item_dict("item-2"), _item_dict("item-3")],
        ),
        request=_request(user),
    )

    assert _owners(db_session) == {
        "item-1": user.email,
        "item-2": user.email,
        "item-3": user.email,
    }


@pytest.mark.asyncio
async def test_delete_removes_owner(
    app: FastAPI, user: User, db_session: Session, no_pgstac: None
):
    client = NullGeometryTransactionsClient()
    for item_id in ["item-1", "item-2", "item-3"]:
        await client.create_item(
            collection_id=COLLECTION_ID,
            item=Item(**_item_dict(item_id)),
            request=_request(user),
        )

    await client.delete_item(
        item_id="item-1", collection_id=COLLECTION_ID, request=_request(user)
    )
    assert set(_owners(db_session)) == {"item-2", "item-3"}

    await client.delete_collection(collection_id=COLLECTION_ID, request=_request(user))
    assert _owners(db_session) == {}


@pytest.mark.asyncio
async def test_bulk_upsert_keeps_existing_owner(
    app: FastAPI, user: User, db_session: Session, no_pgstac: None
):
    _give_role(db_session, user, Role.COLLECTION_DATA_STEWARD, COLLECTION_ID)
    _set_owner(db_session, "existing", "someone.else@deltares.nl")

    await OwnerTrackingBulkTransactionsClient().bulk_item_insert(
        items=Items(
            items={"existing": _item_dict("existing"), "new": _item_dict("new")},
            method=BulkTransactionMethod.UPSERT,
        ),
        request=_request(user),
    )

    assert _owners(db_session) == {
        "existing": "someone.else@deltares.nl",
        "new": user.email,
    }


def test_whole_app_role_allows_creating_items_in_any_collection(
    app: FastAPI, user: User, db_session: Session
):
    _give_role(db_session, user, Role.DATA_PRODUCER, None)

    user_has_collection_permission(Permission.ItemCreate)(
        collection_id=COLLECTION_ID, user=user, session=db_session
    )
    with pytest.raises(HTTPException) as error:
        user_has_collection_permission(Permission.ItemDelete)(
            collection_id=COLLECTION_ID, user=user, session=db_session
        )
    assert error.value.status_code == 403


def test_whole_app_role_only_edits_own_items(
    app: FastAPI, user: User, db_session: Session
):
    _give_role(db_session, user, Role.DATA_PRODUCER, None)
    _set_owner(db_session, "mine", user.email.upper())
    _set_owner(db_session, "theirs", "someone.else@deltares.nl")
    check = user_can_update_item()

    check(collection_id=COLLECTION_ID, item_id="mine", user=user, session=db_session)
    for item_id in ["theirs", "no-owner-recorded"]:
        with pytest.raises(HTTPException) as error:
            check(
                collection_id=COLLECTION_ID,
                item_id=item_id,
                user=user,
                session=db_session,
            )
        assert error.value.status_code == 403
        assert "can only edit items they created" in error.value.detail


def test_collection_role_edits_any_item(
    app: FastAPI, user: User, db_session: Session
):
    _give_role(db_session, user, Role.DATA_PRODUCER, COLLECTION_ID)
    _set_owner(db_session, "theirs", "someone.else@deltares.nl")

    user_can_update_item()(
        collection_id=COLLECTION_ID, item_id="theirs", user=user, session=db_session
    )


@pytest.mark.asyncio
async def test_bulk_upsert_needs_collection_role(
    app: FastAPI, user: User, db_session: Session, no_pgstac: None
):
    _give_role(db_session, user, Role.DATA_PRODUCER, None)
    _set_owner(db_session, "theirs", "someone.else@deltares.nl")

    with pytest.raises(HTTPException) as error:
        await OwnerTrackingBulkTransactionsClient().bulk_item_insert(
            items=Items(
                items={"theirs": _item_dict("theirs")},
                method=BulkTransactionMethod.UPSERT,
            ),
            request=_request(user),
        )
    assert error.value.status_code == 403
    assert _owners(db_session) == {"theirs": "someone.else@deltares.nl"}


def test_collection_permissions_include_whole_app_item_permissions(
    app: FastAPI, user: User, db_session: Session
):
    _give_role(db_session, user, Role.DATA_PRODUCER, None)
    _give_role(db_session, user, Role.ADMIN, None)

    permissions = RBACClient().get_permissions_on_collection(
        COLLECTION_ID, user, db_session
    )

    assert set(permissions) == {Permission.ItemCreate, Permission.ItemUpdate}