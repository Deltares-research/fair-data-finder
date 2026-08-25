"""Custom transactions client that allows null geometry on STAC Items.

The upstream ``stac_fastapi.pgstac.transactions.TransactionsClient`` rejects
items whose ``geometry`` field is ``None``.  That behaviour was added in
``stac-fastapi-pgstac`` to work around a pgSTAC DB constraint, but the STAC
spec explicitly allows null geometry for items that have no spatial extent.

This subclass removes only that single guard; all other validations (id
character check, extension validation, collection/item-id consistency) are
kept intact.
"""

from fastapi import Request
from stac_fastapi.pgstac.transactions import TransactionsClient
from stac_fastapi.types import stac as stac_types
from fastapi import HTTPException


class NullGeometryTransactionsClient(TransactionsClient):
    """TransactionsClient that permits ``geometry: null`` on STAC Items."""

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
