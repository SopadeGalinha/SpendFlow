from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional
from uuid import UUID, uuid4

from sqlmodel import (
    Column,
    DateTime,
    Field,
    Numeric,
    Relationship,
    SQLModel,
)

if TYPE_CHECKING:
    from .calendar import RecurringRule
    from .transaction import Transaction
    from .user import User


class Account(SQLModel, table=True):
    """Financial container (bank account, wallet, savings)."""

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str = Field(
        nullable=False,
        description="Account name, e.g., 'Main Checking'",
    )
    balance: Decimal = Field(
        default=Decimal("0.00"),
        sa_column=Column(
            Numeric(12, 2),
            nullable=False,
            server_default="0.00",
        ),
    )

    user_id: UUID = Field(foreign_key="user.id", index=True)

    deleted_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
        description="Timestamp when the account was soft-deleted",
    )

    user: "User" = Relationship(back_populates="accounts")
    recurring_rules: List["RecurringRule"] = Relationship(
        back_populates="account",
    )
    transactions: List["Transaction"] = Relationship(
        back_populates="account",
    )


__all__ = ["Account"]
