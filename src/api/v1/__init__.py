from .account import router as accounts
from .auth import router as auth
from .budget import router as budgets
from .calendar import router as calendar
from .category import router as categories
from .transaction import router as transactions

__all__ = [
    "accounts",
    "auth",
    "budgets",
    "calendar",
    "categories",
    "transactions",
]
