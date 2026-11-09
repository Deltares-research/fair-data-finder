import pytest
from api.database.models import ItemOwner, User
from api.extensions.core.sso_auth_extension import COOKIE_NAME
from api.extensions.core.transactions_client import (
    NullGeometryTransactionsClient,
    OwnerTrackingBulkTransactionsClient,
)
from fastapi import FastAPI
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
    db_session.add(
        ItemOwner(
            collection_id=COLLECTION_ID,
            item_id="existing",
            owner_email="someone.else@deltares.nl",
        )
    )
    db_session.commit()

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
