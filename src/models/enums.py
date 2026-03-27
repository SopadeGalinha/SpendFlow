from enum import Enum


class WeekendAdjustment(str, Enum):
    """Defines how to handle transactions falling on weekends."""

    KEEP = "keep"  # Keep on the same date
    FOLLOWING = "following"  # Move to the next Monday
    PRECEDING = "preceding"  # Move to the previous Friday


class AccountType(str, Enum):
    """Supported V1 asset account types."""

    CHECKING = "checking"
    SAVINGS = "savings"


class TransactionType(str, Enum):
    """Standard financial transaction types."""

    INCOME = "income"
    EXPENSE = "expense"


class TransactionKind(str, Enum):
    """Explains why a persisted ledger entry exists."""

    REGULAR = "regular"
    OPENING_BALANCE = "opening_balance"
    ADJUSTMENT = "adjustment"
    TRANSFER = "transfer"


class CategoryType(str, Enum):
    """Category types supported by budgeting and reporting."""

    INCOME = "income"
    EXPENSE = "expense"
    TRANSFER = "transfer"


class Frequency(str, Enum):
    """Recurrence frequency for virtual projections."""

    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"


class BudgetScope(str, Enum):
    """How a budget applies to expense categorization."""

    CATEGORY = "category"
    GROUP = "group"


class BudgetStatus(str, Enum):
    """Derived lifecycle state for a budget based on its period."""

    ACTIVE = "active"
    UPCOMING = "upcoming"
    ARCHIVED = "archived"
