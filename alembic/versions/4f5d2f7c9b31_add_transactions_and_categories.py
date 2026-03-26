"""add transactions and categories

Revision ID: 4f5d2f7c9b31
Revises: d62f86d08d40
Create Date: 2026-03-25 00:00:00.000000

"""

from typing import Sequence, Union
from uuid import uuid4

import sqlalchemy as sa
import sqlmodel
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "4f5d2f7c9b31"
down_revision: Union[str, Sequence[str], None] = "d62f86d08d40"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    category_type = postgresql.ENUM(
        "INCOME",
        "EXPENSE",
        "TRANSFER",
        name="categorytype",
        create_type=False,
    )
    transaction_type = postgresql.ENUM(
        "INCOME",
        "EXPENSE",
        name="transactiontype",
        create_type=False,
    )

    category_type.create(bind, checkfirst=True)

    op.create_table(
        "category_groups",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("slug", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column(
            "type",
            category_type,
            nullable=False,
        ),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("is_system", sa.Boolean(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_category_groups_slug"),
        "category_groups",
        ["slug"],
        unique=False,
    )
    op.create_index(
        op.f("ix_category_groups_type"),
        "category_groups",
        ["type"],
        unique=False,
    )
    op.create_index(
        op.f("ix_category_groups_user_id"),
        "category_groups",
        ["user_id"],
        unique=False,
    )

    op.create_table(
        "transactions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "description",
            sqlmodel.sql.sqltypes.AutoString(),
            nullable=False,
        ),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column(
            "type",
            transaction_type,
            nullable=False,
        ),
        sa.Column("transaction_date", sa.Date(), nullable=False),
        sa.Column("account_id", sa.Uuid(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["account_id"], ["account.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_transactions_account_id"),
        "transactions",
        ["account_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_transactions_transaction_date"),
        "transactions",
        ["transaction_date"],
        unique=False,
    )

    op.create_table(
        "categories",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("slug", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column(
            "type",
            category_type,
            nullable=False,
        ),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("is_system", sa.Boolean(), nullable=False),
        sa.Column("is_transfer", sa.Boolean(), nullable=False),
        sa.Column("exclude_from_budget", sa.Boolean(), nullable=False),
        sa.Column("group_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["group_id"], ["category_groups.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_categories_group_id"),
        "categories",
        ["group_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_categories_slug"),
        "categories",
        ["slug"],
        unique=False,
    )
    op.create_index(
        op.f("ix_categories_type"),
        "categories",
        ["type"],
        unique=False,
    )
    op.create_index(
        op.f("ix_categories_user_id"),
        "categories",
        ["user_id"],
        unique=False,
    )
    op.add_column(
        "transactions",
        sa.Column("category_id", sa.Uuid(), nullable=True),
    )
    op.create_foreign_key(
        "fk_transactions_category_id_categories",
        "transactions",
        "categories",
        ["category_id"],
        ["id"],
    )
    op.create_index(
        op.f("ix_transactions_category_id"),
        "transactions",
        ["category_id"],
        unique=False,
    )

    category_groups_table = sa.table(
        "category_groups",
        sa.column("id", sa.Uuid()),
        sa.column("name", sa.String()),
        sa.column("slug", sa.String()),
        sa.column("type", sa.String()),
        sa.column("sort_order", sa.Integer()),
        sa.column("is_system", sa.Boolean()),
        sa.column("user_id", sa.Uuid()),
    )
    categories_table = sa.table(
        "categories",
        sa.column("id", sa.Uuid()),
        sa.column("name", sa.String()),
        sa.column("slug", sa.String()),
        sa.column("type", sa.String()),
        sa.column("sort_order", sa.Integer()),
        sa.column("is_system", sa.Boolean()),
        sa.column("is_transfer", sa.Boolean()),
        sa.column("exclude_from_budget", sa.Boolean()),
        sa.column("group_id", sa.Uuid()),
        sa.column("user_id", sa.Uuid()),
    )

    default_groups = [
        {
            "id": uuid4(),
            "name": "Income",
            "slug": "income",
            "type": "INCOME",
            "sort_order": 10,
            "categories": [
                "Salary",
                "Freelance",
                "Business",
                "Investment",
                "Bonus",
                "Gift",
                "Refund",
                "Other Income",
            ],
        },
        {
            "id": uuid4(),
            "name": "Home",
            "slug": "home",
            "type": "EXPENSE",
            "sort_order": 20,
            "categories": ["Housing", "Utilities", "Insurance"],
        },
        {
            "id": uuid4(),
            "name": "Living",
            "slug": "living",
            "type": "EXPENSE",
            "sort_order": 30,
            "categories": [
                "Groceries",
                "Transport",
                "Health",
                "Education",
                "Eating Out",
            ],
        },
        {
            "id": uuid4(),
            "name": "Lifestyle",
            "slug": "lifestyle",
            "type": "EXPENSE",
            "sort_order": 40,
            "categories": [
                "Entertainment",
                "Shopping",
                "Subscriptions",
                "Travel",
            ],
        },
        {
            "id": uuid4(),
            "name": "Financial",
            "slug": "financial",
            "type": "EXPENSE",
            "sort_order": 50,
            "categories": ["Taxes", "Savings", "Debt Payment"],
        },
        {
            "id": uuid4(),
            "name": "Pets",
            "slug": "pets",
            "type": "EXPENSE",
            "sort_order": 60,
            "categories": ["Pets"],
        },
        {
            "id": uuid4(),
            "name": "Transfers",
            "slug": "transfers",
            "type": "TRANSFER",
            "sort_order": 70,
            "categories": ["Transfer", "Credit Card Payment"],
        },
    ]

    op.bulk_insert(
        category_groups_table,
        [
            {
                "id": group["id"],
                "name": group["name"],
                "slug": group["slug"],
                "type": group["type"],
                "sort_order": group["sort_order"],
                "is_system": True,
                "user_id": None,
            }
            for group in default_groups
        ],
    )

    category_rows = []
    for group_index, group in enumerate(default_groups, start=1):
        is_transfer = group["type"] == "TRANSFER"
        for category_index, category_name in enumerate(
            group["categories"],
            start=1,
        ):
            category_rows.append(
                {
                    "id": uuid4(),
                    "name": category_name,
                    "slug": category_name.lower().replace(" ", "_"),
                    "type": group["type"],
                    "sort_order": (group_index * 100) + category_index,
                    "is_system": True,
                    "is_transfer": is_transfer,
                    "exclude_from_budget": is_transfer,
                    "group_id": group["id"],
                    "user_id": None,
                }
            )

    op.bulk_insert(categories_table, category_rows)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_categories_user_id"), table_name="categories")
    op.drop_index(op.f("ix_categories_type"), table_name="categories")
    op.drop_index(op.f("ix_categories_slug"), table_name="categories")
    op.drop_index(op.f("ix_categories_group_id"), table_name="categories")
    op.drop_index(
        op.f("ix_transactions_category_id"),
        table_name="transactions",
    )
    op.drop_constraint(
        "fk_transactions_category_id_categories",
        "transactions",
        type_="foreignkey",
    )
    op.drop_column("transactions", "category_id")
    op.drop_table("categories")

    op.drop_index(
        op.f("ix_transactions_transaction_date"),
        table_name="transactions",
    )
    op.drop_index(
        op.f("ix_transactions_account_id"),
        table_name="transactions",
    )
    op.drop_table("transactions")

    op.drop_index(
        op.f("ix_category_groups_user_id"),
        table_name="category_groups",
    )
    op.drop_index(
        op.f("ix_category_groups_type"),
        table_name="category_groups",
    )
    op.drop_index(
        op.f("ix_category_groups_slug"),
        table_name="category_groups",
    )
    op.drop_table("category_groups")

    sa.Enum(name="categorytype").drop(op.get_bind(), checkfirst=True)
