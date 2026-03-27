from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import Enum as SQLEnum
from sqlalchemy import Index, text
from sqlmodel import (
    CheckConstraint,
    Column,
    Date,
    DateTime,
    Field,
    Numeric,
    Relationship,
    SQLModel,
    func,
)

from src.models.enums import BudgetScope

if TYPE_CHECKING:
    from src.models.category import Category
    from src.models.category_group import CategoryGroup
    from src.models.user import User


class Budget(SQLModel, table=True):
    """Budget target scoped to one category or one category group."""

    __tablename__ = "budgets"
    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_budgets_amount_positive"),
        CheckConstraint(
            "period_end >= period_start",
            name="ck_budgets_period_valid",
        ),
        CheckConstraint(
            "((category_id IS NOT NULL AND category_group_id IS NULL) OR "
            "(category_id IS NULL AND category_group_id IS NOT NULL))",
            name="ck_budgets_single_scope_target",
        ),
        Index(
            "uq_budgets_user_category_period",
            "user_id",
            "category_id",
            "period_start",
            "period_end",
            unique=True,
            sqlite_where=text(
                "category_id IS NOT NULL AND category_group_id IS NULL"
            ),
            postgresql_where=text(
                "category_id IS NOT NULL AND category_group_id IS NULL"
            ),
        ),
        Index(
            "uq_budgets_user_group_period",
            "user_id",
            "category_group_id",
            "period_start",
            "period_end",
            unique=True,
            sqlite_where=text(
                "category_group_id IS NOT NULL AND category_id IS NULL"
            ),
            postgresql_where=text(
                "category_group_id IS NOT NULL AND category_id IS NULL"
            ),
        ),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str = Field(nullable=False)
    amount: Decimal = Field(
        sa_column=Column(Numeric(12, 2), nullable=False),
    )
    period_start: date = Field(sa_column=Column(Date(), nullable=False))
    period_end: date = Field(sa_column=Column(Date(), nullable=False))
    scope: BudgetScope = Field(
        sa_column=Column(
            SQLEnum(BudgetScope, name="budgetscope"),
            nullable=False,
        )
    )
    category_group_id: UUID | None = Field(
        default=None,
        foreign_key="category_groups.id",
        index=True,
    )
    category_id: UUID | None = Field(
        default=None,
        foreign_key="categories.id",
        index=True,
    )
    user_id: UUID = Field(foreign_key="user.id", index=True)
    created_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True),
            nullable=False,
            server_default=func.now(),
        )
    )
    updated_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True),
            nullable=False,
            server_default=func.now(),
            onupdate=func.now(),
        )
    )

    user: "User" = Relationship()
    category_group: "CategoryGroup" = Relationship()
    category: "Category" = Relationship()


__all__ = ["Budget"]
