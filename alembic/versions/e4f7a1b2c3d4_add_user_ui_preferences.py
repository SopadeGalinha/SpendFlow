"""add user ui preferences

Revision ID: e4f7a1b2c3d4
Revises: c3d4e5f6a7b8
Create Date: 2026-03-31 12:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "e4f7a1b2c3d4"
down_revision: Union[str, Sequence[str], None] = "c3d4e5f6a7b8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "user",
        sa.Column("ui_preferences", sa.JSON(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("user", "ui_preferences")
