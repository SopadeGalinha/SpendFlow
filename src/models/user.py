from datetime import datetime
from typing import Optional, List, TYPE_CHECKING
from uuid import UUID, uuid4
from enum import Enum
from sqlmodel import (  # type: ignore
    SQLModel,
    Field,
    Relationship,
    Column,
    DateTime,
    func,
)

if TYPE_CHECKING:
    from .account import Account


class WeekendAdjustment(str, Enum):
    """Defines how to handle transactions falling on weekends."""

    KEEP = "keep"  # Keep on the same date
    FOLLOWING = "following"  # Move to the next Monday
    PRECEDING = "preceding"  # Move to the previous Friday


class TransactionType(str, Enum):
    """Standard financial transaction types."""

    INCOME = "income"
    EXPENSE = "expense"


class Frequency(str, Enum):
    """Recurrence frequency for virtual projections."""

    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"


class User(SQLModel, table=True):
    """
    Core User model for SpendFlow.
    Includes SaaS-ready fields like timezone and currency.
    """

    # Relationships
    accounts: List["Account"] = Relationship(back_populates="user")

    id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
        index=True,
        description="Unique identifier for the user",
    )
    username: str = Field(index=True, unique=True, nullable=False)
    email: str = Field(index=True, unique=True, nullable=False)
    hashed_password: str = Field(nullable=False)

    # SaaS & Regional Settings
    city: Optional[str] = Field(default=None)
    timezone: str = Field(
        default="UTC",
        description="User's local timezone (e.g., Europe/Lisbon)",
    )
    currency: str = Field(
        default="EUR",
        description="Primary currency for display",
    )

    default_weekend_adjustment: WeekendAdjustment = Field(
        default=WeekendAdjustment.KEEP,
        description="Default rule for weekend date shifting",
    )
    created_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True), nullable=False, server_default=func.now()
        ),
        description="Timestamp when the user was created",
    )
    updated_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True),
            nullable=False,
            server_default=func.now(),
            onupdate=func.now(),
        ),
        description="Timestamp when the user was last updated",
    )

    # Relationships
    accounts: List["Account"] = Relationship(back_populates="user")
