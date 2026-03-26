"""add deleted_at to recurring rules

Revision ID: a7b2c1d4e5f6
Revises: 9c6f5d7b8a12
Create Date: 2026-03-26 15:35:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "a7b2c1d4e5f6"
down_revision: Union[str, Sequence[str], None] = "9c6f5d7b8a12"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "recurringrule",
        sa.Column(
            "deleted_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("recurringrule", "deleted_at")
