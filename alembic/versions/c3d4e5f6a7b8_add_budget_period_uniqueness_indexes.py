"""add budget period uniqueness indexes

Revision ID: c3d4e5f6a7b8
Revises: b1c2d3e4f5a6
Create Date: 2026-03-27 10:30:00.000000

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c3d4e5f6a7b8"
down_revision: Union[str, Sequence[str], None] = "b1c2d3e4f5a6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(
        "uq_budgets_user_category_period",
        "budgets",
        ["user_id", "category_id", "period_start", "period_end"],
        unique=True,
        postgresql_where=(
            "category_id IS NOT NULL AND category_group_id IS NULL"
        ),
    )
    op.create_index(
        "uq_budgets_user_group_period",
        "budgets",
        ["user_id", "category_group_id", "period_start", "period_end"],
        unique=True,
        postgresql_where=(
            "category_group_id IS NOT NULL AND category_id IS NULL"
        ),
    )


def downgrade() -> None:
    op.drop_index("uq_budgets_user_group_period", table_name="budgets")
    op.drop_index("uq_budgets_user_category_period", table_name="budgets")
