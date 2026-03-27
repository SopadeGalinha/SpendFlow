"""v1 ledger, budgets, and constraints

Revision ID: b1c2d3e4f5a6
Revises: a7b2c1d4e5f6
Create Date: 2026-03-26 20:30:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "b1c2d3e4f5a6"
down_revision: Union[str, Sequence[str], None] = "a7b2c1d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()

    account_type = postgresql.ENUM(
        "CHECKING",
        "SAVINGS",
        name="accounttype",
        create_type=False,
    )
    transaction_kind = postgresql.ENUM(
        "REGULAR",
        "OPENING_BALANCE",
        "ADJUSTMENT",
        "TRANSFER",
        name="transactionkind",
        create_type=False,
    )
    budget_scope = postgresql.ENUM(
        "CATEGORY",
        "GROUP",
        name="budgetscope",
        create_type=False,
    )

    account_type.create(bind, checkfirst=True)
    transaction_kind.create(bind, checkfirst=True)
    budget_scope.create(bind, checkfirst=True)

    op.add_column(
        "account",
        sa.Column(
            "account_type",
            account_type,
            nullable=False,
            server_default="CHECKING",
        ),
    )
    op.alter_column(
        "account",
        "account_type",
        server_default=None,
        existing_type=account_type,
    )
    op.create_check_constraint(
        "ck_account_balance_non_negative",
        "account",
        "balance >= 0",
    )

    op.add_column(
        "transactions",
        sa.Column(
            "kind",
            transaction_kind,
            nullable=False,
            server_default="REGULAR",
        ),
    )
    op.alter_column(
        "transactions",
        "kind",
        server_default=None,
        existing_type=transaction_kind,
    )
    op.add_column(
        "transactions",
        sa.Column("transfer_group_id", sa.Uuid(), nullable=True),
    )
    op.create_index(
        "ix_transactions_transfer_group_id",
        "transactions",
        ["transfer_group_id"],
        unique=False,
    )
    op.create_check_constraint(
        "ck_transactions_amount_positive",
        "transactions",
        "amount > 0",
    )

    op.create_check_constraint(
        "ck_recurringrule_amount_positive",
        "recurringrule",
        "amount > 0",
    )
    op.create_check_constraint(
        "ck_recurringrule_interval_positive",
        "recurringrule",
        '"interval" >= 1',
    )

    op.create_unique_constraint(
        "uq_category_groups_slug_type",
        "category_groups",
        ["slug", "type"],
    )
    op.create_unique_constraint(
        "uq_categories_group_slug",
        "categories",
        ["group_id", "slug"],
    )

    op.execute(
        'CREATE UNIQUE INDEX IF NOT EXISTS uq_user_email_lower '
        'ON "user" (lower(email))'
    )
    op.execute(
        'CREATE UNIQUE INDEX IF NOT EXISTS uq_user_username_lower '
        'ON "user" (lower(username))'
    )

    op.create_table(
        "budgets",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("period_start", sa.Date(), nullable=False),
        sa.Column("period_end", sa.Date(), nullable=False),
        sa.Column("scope", budget_scope, nullable=False),
        sa.Column("category_group_id", sa.Uuid(), nullable=True),
        sa.Column("category_id", sa.Uuid(), nullable=True),
        sa.Column("user_id", sa.Uuid(), nullable=False),
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
        sa.ForeignKeyConstraint(["category_group_id"], ["category_groups.id"]),
        sa.ForeignKeyConstraint(["category_id"], ["categories.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("amount > 0", name="ck_budgets_amount_positive"),
        sa.CheckConstraint(
            "period_end >= period_start",
            name="ck_budgets_period_valid",
        ),
        sa.CheckConstraint(
            "((category_id IS NOT NULL AND category_group_id IS NULL) OR "
            "(category_id IS NULL AND category_group_id IS NOT NULL))",
            name="ck_budgets_single_scope_target",
        ),
    )
    op.create_index("ix_budgets_category_group_id", "budgets", ["category_group_id"])
    op.create_index("ix_budgets_category_id", "budgets", ["category_id"])
    op.create_index("ix_budgets_user_id", "budgets", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_budgets_user_id", table_name="budgets")
    op.drop_index("ix_budgets_category_id", table_name="budgets")
    op.drop_index("ix_budgets_category_group_id", table_name="budgets")
    op.drop_table("budgets")

    op.execute('DROP INDEX IF EXISTS uq_user_username_lower')
    op.execute('DROP INDEX IF EXISTS uq_user_email_lower')

    op.drop_constraint(
        "uq_categories_group_slug",
        "categories",
        type_="unique",
    )
    op.drop_constraint(
        "uq_category_groups_slug_type",
        "category_groups",
        type_="unique",
    )

    op.drop_constraint(
        "ck_recurringrule_interval_positive",
        "recurringrule",
        type_="check",
    )
    op.drop_constraint(
        "ck_recurringrule_amount_positive",
        "recurringrule",
        type_="check",
    )

    op.drop_constraint(
        "ck_transactions_amount_positive",
        "transactions",
        type_="check",
    )
    op.drop_index(
        "ix_transactions_transfer_group_id",
        table_name="transactions",
    )
    op.drop_column("transactions", "transfer_group_id")
    op.drop_column("transactions", "kind")

    op.drop_constraint(
        "ck_account_balance_non_negative",
        "account",
        type_="check",
    )
    op.drop_column("account", "account_type")

    budget_scope = postgresql.ENUM(name="budgetscope")
    transaction_kind = postgresql.ENUM(name="transactionkind")
    account_type = postgresql.ENUM(name="accounttype")
    budget_scope.drop(op.get_bind(), checkfirst=True)
    transaction_kind.drop(op.get_bind(), checkfirst=True)
    account_type.drop(op.get_bind(), checkfirst=True)