"""add interval to recurring rules

Revision ID: 9c6f5d7b8a12
Revises: 4f5d2f7c9b31
Create Date: 2026-03-26 15:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "9c6f5d7b8a12"
down_revision: Union[str, Sequence[str], None] = "4f5d2f7c9b31"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "recurringrule",
        sa.Column(
            "interval",
            sa.Integer(),
            nullable=False,
            server_default="1",
        ),
    )
    op.alter_column(
        "recurringrule",
        "interval",
        server_default=None,
        existing_type=sa.Integer(),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("recurringrule", "interval")
