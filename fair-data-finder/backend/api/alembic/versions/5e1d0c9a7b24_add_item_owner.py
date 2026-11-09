"""add item owner

Revision ID: 5e1d0c9a7b24
Revises: c7b2e5a9d413
Create Date: 2026-11-09

"""

from typing import Sequence, Union

import sqlalchemy as sa
import sqlmodel
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "5e1d0c9a7b24"
down_revision: Union[str, None] = "c7b2e5a9d413"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "itemowner",
        sa.Column("collection_id", sqlmodel.AutoString(), nullable=False),
        sa.Column("item_id", sqlmodel.AutoString(), nullable=False),
        sa.Column("owner_email", sqlmodel.AutoString(), nullable=False),
        sa.PrimaryKeyConstraint("collection_id", "item_id"),
    )


def downgrade() -> None:
    op.drop_table("itemowner")
