from datetime import date
from decimal import Decimal
from typing import Optional
from uuid import UUID, uuid4
from sqlmodel import (
    Column,
    Numeric,
    SQLModel,
    Field,
    Relationship,
)

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from src.models import Account
from src.models import Frequency, TransactionType, WeekendAdjustment


class RecurringRule(SQLModel, table=True):
    """
    The 'Virtual Template'. This does NOT store actual transactions.
    It provides the logic for the Calendar Service to project future cash flow.
    """

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    description: str = Field(nullable=False)
    amount: Decimal = Field(sa_column=Column(Numeric(12, 2), nullable=False))
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
    account: "Account" = Relationship(back_populates="recurring_rules")


__all__ = ["RecurringRule"]
