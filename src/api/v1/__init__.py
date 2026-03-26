from .account import router as accounts
from .auth import router as auth
from .calendar import router as calendar
from .category import router as categories
from .transaction import router as transactions

__all__ = ["accounts", "calendar", "auth", "categories", "transactions"]
