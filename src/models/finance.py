from datetime import date
from typing import Optional, List
from uuid import UUID, uuid4
from sqlmodel import SQLModel, Field, Relationship  # type: ignore
from .user import User, TransactionType, WeekendAdjustment, Frequency


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
    balance: float = Field(
        default=0.0,
        description="Current real-time balance",
    )

    user_id: UUID = Field(foreign_key="user.id", index=True)

    # Relationships
    user: User = Relationship(back_populates="accounts")
    recurring_rules: List["RecurringRule"] = Relationship(
        back_populates="account",
    )


class RecurringRule(SQLModel, table=True):
    """
    The 'Virtual Template'. This does NOT store actual transactions.
    It provides the logic for the Calendar Service to project future cash flow.
    """

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    description: str = Field(nullable=False)
    amount: float = Field(nullable=False)
    type: TransactionType = Field(nullable=False)
    frequency: Frequency = Field(default=Frequency.MONTHLY)

    # Dates are 'date' objects (YYYY-MM-DD) as they represent calendar days
    start_date: date = Field(nullable=False)
    end_date: Optional[date] = Field(default=None)

    # Specific rule for this transaction (overrides User default)
    weekend_adjustment: WeekendAdjustment = Field(
        default=WeekendAdjustment.KEEP,
        description="Specific adjustment for this rule",
    )

    account_id: UUID = Field(foreign_key="account.id", index=True)

    # Relationships
    account: Account = Relationship(back_populates="recurring_rules")
