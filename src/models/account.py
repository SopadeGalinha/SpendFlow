from datetime import datetime
from decimal import Decimal
from typing import Optional, List, TYPE_CHECKING
from uuid import UUID, uuid4
from sqlmodel import (
    Column,
    DateTime,
    Numeric,
    SQLModel,
    Field,
    Relationship,
)

if TYPE_CHECKING:
    from .calendar import RecurringRule
    from .user import User


class Account(SQLModel, table=True):
    """
    Represents a financial container (Bank, Wallet, Savings).
    Belongs to a specific User.
    """

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

    # Soft Delete
    deleted_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
        description="If set, the account is considered deleted",
    )

    user: "User" = Relationship(back_populates="accounts")
    recurring_rules: List["RecurringRule"] = Relationship(
        back_populates="account",
    )
    user: "User" = Relationship(back_populates="accounts")


__all__ = ["Account"]
