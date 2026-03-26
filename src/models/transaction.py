from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlmodel import (
    Column,
    Date,
    DateTime,
    Field,
    Numeric,
    Relationship,
    SQLModel,
    func,
)

from src.models.enums import TransactionType

if TYPE_CHECKING:
    from src.models.account import Account
    from src.models.category import Category


class Transaction(SQLModel, table=True):
    """Persisted financial transaction that affects an account balance."""

    __tablename__ = "transactions"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    description: str = Field(nullable=False)
    amount: Decimal = Field(
        sa_column=Column(Numeric(12, 2), nullable=False),
    )
    type: TransactionType = Field(nullable=False)
    transaction_date: date = Field(
        sa_column=Column(Date(), nullable=False, index=True),
    )
    account_id: UUID = Field(foreign_key="account.id", index=True)
    category_id: UUID | None = Field(
        default=None,
        foreign_key="categories.id",
        index=True,
    )
    deleted_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
    )
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

    account: "Account" = Relationship(back_populates="transactions")
    category: "Category" = Relationship(back_populates="transactions")


__all__ = ["Transaction"]
