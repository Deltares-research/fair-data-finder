"""Allow null geometry in pgstac items and enable isNull(geometry) CQL2 filter.

Drop the NOT NULL constraint on pgstac.items.geometry so that spec-compliant
items without a spatial extent can be stored.  Also add an additive
``pgstac.to_text(geometry)`` overload so that the CQL2 ``isNull(geometry)``
operator (which pgSTAC renders to ``to_text(geometry) IS NULL``) resolves and
executes without error.

The overload is a *new* function signature that pgSTAC itself never defines
(it only ships ``to_text(jsonb)``), so a future ``pypgstac migrate`` will not
clobber it.

Revision ID: f8a3c5e92b01
Revises: 83d66cb945c2
Create Date: 2025-07-02

"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "f8a3c5e92b01"
down_revision: Union[str, None] = "83d66cb945c2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop NOT NULL so geometry-less items can be stored (STAC spec allows null geometry).
    # Wrapped in a DO block so the migration is idempotent on databases that
    # already have the constraint dropped.
    op.execute(
        """
        DO $$
        BEGIN
            ALTER TABLE pgstac.items ALTER COLUMN geometry DROP NOT NULL;
        EXCEPTION
            WHEN others THEN
                -- Constraint was already absent; ignore.
                NULL;
        END;
        $$;
        """
    )

    # Add an additive to_text(geometry) overload so that pgSTAC's CQL2 engine
    # can render isNull(geometry) → to_text(geometry) IS NULL without error.
    op.execute(
        """
        CREATE OR REPLACE FUNCTION pgstac.to_text(geometry)
            RETURNS text
            LANGUAGE sql
            IMMUTABLE
        AS $f$ SELECT ST_AsText($1) $f$;
        """
    )

    # Add a to_text(text) overload so PostgreSQL's function resolution prefers
    # it over to_text(jsonb) or to_text(geometry) when called with an untyped
    # string literal (type "unknown").  Without this, adding to_text(geometry)
    # causes an AmbiguousFunctionError for calls like to_text('%%').
    op.execute(
        """
        CREATE OR REPLACE FUNCTION pgstac.to_text(text)
            RETURNS text
            LANGUAGE sql
            IMMUTABLE PARALLEL SAFE STRICT
        AS $f$ SELECT $1 $f$;
        """
    )


def downgrade() -> None:
    op.execute("DROP FUNCTION IF EXISTS pgstac.to_text(geometry);")
    op.execute("DROP FUNCTION IF EXISTS pgstac.to_text(text);")

    # Re-add NOT NULL only when all existing items already have geometry.
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pgstac.items WHERE geometry IS NULL LIMIT 1
            ) THEN
                ALTER TABLE pgstac.items ALTER COLUMN geometry SET NOT NULL;
            END IF;
        END;
        $$;
        """
    )
