from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional
from uuid import UUID, uuid4

from sqlmodel import (
    Column,
    DateTime,
    Field,
    Numeric,
    Relationship,
    SQLModel,
)

from src.models.enums import Frequency, TransactionType, WeekendAdjustment

if TYPE_CHECKING:
    from src.models.account import Account


class RecurringRule(SQLModel, table=True):
    """Virtual template for recurring transactions.
    Provides logic for projecting future cash flow.
    """

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    description: str = Field(nullable=False)
    amount: Decimal = Field(sa_column=Column(Numeric(12, 2), nullable=False))
    type: TransactionType = Field(nullable=False)
    frequency: Frequency = Field(default=Frequency.MONTHLY)

    start_date: date = Field(nullable=False)
    end_date: Optional[date] = Field(default=None)

    weekend_adjustment: WeekendAdjustment = Field(
        default=WeekendAdjustment.KEEP,
        description="Adjustment rule for weekend dates",
    )

    account_id: UUID = Field(foreign_key="account.id", index=True)

    deleted_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
        description="Soft delete timestamp",
    )

    account: "Account" = Relationship(back_populates="recurring_rules")


__all__ = ["RecurringRule"]
