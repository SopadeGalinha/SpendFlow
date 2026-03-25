from enum import Enum


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
