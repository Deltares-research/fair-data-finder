"""Custom transactions clients.

``NullGeometryTransactionsClient`` allows null geometry on STAC Items.

The upstream ``stac_fastapi.pgstac.transactions.TransactionsClient`` rejects
items whose ``geometry`` field is ``None``.  That behaviour was added in
``stac-fastapi-pgstac`` to work around a pgSTAC DB constraint, but the STAC
spec explicitly allows null geometry for items that have no spatial extent.

This subclass removes only that single guard; all other validations (id
character check, extension validation, collection/item-id consistency) are
kept intact.

Both clients also record who created each item in the ``ItemOwner`` table.
"""

from typing import Any, Iterable

from fastapi import Request
from sqlalchemy import delete
from sqlmodel import Session
from starlette.concurrency import run_in_threadpool
from stac_fastapi.extensions.third_party.bulk_transactions import (
    BulkTransactionMethod,
    Items,
)
from stac_fastapi.pgstac.transactions import BulkTransactionsClient, TransactionsClient
from stac_fastapi.types import stac as stac_types
from fastapi import HTTPException
from stac_pydantic import Item, ItemCollection

from api.database.db import create_db_engine
from api.database.models import ItemOwner
from api.extensions.core.sso_auth_extension import COOKIE_NAME, SSOAuthExtension


def _current_user_email(request: Request) -> str:
    """Return the email of the logged-in user, read from the SSO cookie."""
    return SSOAuthExtension.get_logged_user(request.cookies.get(COOKIE_NAME)).email


def record_item_owners(
    collection_id: str,
    item_ids: Iterable[str],
    owner_email: str,
    overwrite: bool,
) -> None:
    """Store ``owner_email`` as the owner of the given items.

    Args:
        collection_id: collection the items belong to.
        item_ids: ids of the items.
        owner_email: email of the user who created the items.
        overwrite: replace an existing owner. Use False when an item may
            already exist (upsert), so the original owner is kept.
    """
    with Session(create_db_engine()) as session:
        for item_id in dict.fromkeys(item_ids):
            existing = session.get(ItemOwner, (collection_id, item_id))
            if existing is None:
                session.add(
                    ItemOwner(
                        collection_id=collection_id,
                        item_id=item_id,
                        owner_email=owner_email,
                    )
                )
            elif overwrite:
                existing.owner_email = owner_email
                session.add(existing)
        session.commit()


def delete_item_owners(collection_id: str, item_id: str | None = None) -> None:
    """Remove the owner of one item, or of all items in a collection."""
    with Session(create_db_engine()) as session:
        statement = delete(ItemOwner).where(ItemOwner.collection_id == collection_id)
        if item_id is not None:
            statement = statement.where(ItemOwner.item_id == item_id)
        session.execute(statement)
        session.commit()


class NullGeometryTransactionsClient(TransactionsClient):
    """TransactionsClient that permits ``geometry: null`` on STAC Items."""

    async def create_item(  # type: ignore [override]
        self,
        collection_id: str,
        item: Item | ItemCollection,
        request: Request,
        **kwargs: Any,
    ) -> Any:
        """Create one or more items and record the current user as their owner."""
        owner_email = _current_user_email(request)
        response = await super().create_item(
            collection_id=collection_id, item=item, request=request, **kwargs
        )
        if item.type == "FeatureCollection":
            item_ids = [feature.id for feature in item.features]
        else:
            item_ids = [item.id]
        await run_in_threadpool(
            record_item_owners, collection_id, item_ids, owner_email, True
        )
        return response

    async def delete_item(  # type: ignore [override]
        self,
        item_id: str,
        collection_id: str,
        request: Request,
        **kwargs: Any,
    ) -> Any:
        """Delete an item and its owner record."""
        response = await super().delete_item(
            item_id=item_id, collection_id=collection_id, request=request, **kwargs
        )
        await run_in_threadpool(delete_item_owners, collection_id, item_id)
        return response

    async def delete_collection(  # type: ignore [override]
        self,
        collection_id: str,
        request: Request,
        **kwargs: Any,
    ) -> Any:
        """Delete a collection and the owner records of its items."""
        response = await super().delete_collection(
            collection_id=collection_id, request=request, **kwargs
        )
        await run_in_threadpool(delete_item_owners, collection_id)
        return response

    def _validate_item(
        self,
        request: Request,
        item: stac_types.Item,
        collection_id: str,
        expected_item_id: str | None = None,
    ) -> None:
        """Validate item, skipping the null-geometry guard.

        The DB constraint on ``pgstac.items.geometry`` has been dropped via
        the ``f8a3c5e92b01`` Alembic migration, so null geometry is safe to
        store.  All other validation from the parent class is preserved.
        """
        
        body_collection_id = item.get("collection")
        body_item_id = item.get("id")

        self._validate_id(body_item_id, request.app.state.settings)
        self._validate_extensions(item, request.app.state.settings)

        # Null geometry is explicitly allowed by the STAC spec (§7.1).

        if body_collection_id is not None and collection_id != body_collection_id:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Collection ID from path parameter ({collection_id}) does not "
                    f"match Collection ID from Item ({body_collection_id})"
                ),
            )

        if expected_item_id is not None and expected_item_id != body_item_id:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Item ID from path parameter ({expected_item_id}) does not "
                    f"match Item ID from Item ({body_item_id})"
                ),
            )


class OwnerTrackingBulkTransactionsClient(BulkTransactionsClient):
    """BulkTransactionsClient that records the current user as owner of new items."""

    async def bulk_item_insert(  # type: ignore [override]
        self, items: Items, request: Request, **kwargs: Any
    ) -> str:
        """Insert or upsert items and record the current user as owner of new items.

        For upserts the owner of an item that already has one is kept.
        """
        owner_email = _current_user_email(request)
        result = await super().bulk_item_insert(items, request, **kwargs)
        await run_in_threadpool(
            record_item_owners,
            request.path_params["collection_id"],
            list(items.items.keys()),
            owner_email,
            items.method == BulkTransactionMethod.INSERT,
        )
        return result
