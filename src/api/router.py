from fastapi import FastAPI

from src.api.v1 import (
    accounts,
    auth,
    budgets,
    calendar,
    categories,
    transactions,
)


def include_routers(app: FastAPI):
    app.include_router(
        calendar,
        prefix="/api/v1/calendar",
        tags=["Calendar"],
    )
    app.include_router(
        accounts,
        prefix="/api/v1/accounts",
        tags=["Accounts"],
    )
    app.include_router(
        budgets,
        prefix="/api/v1/budgets",
        tags=["Budgets"],
    )
    app.include_router(
        auth,
        prefix="/api/v1/auth",
        tags=["Authentication"],
    )
    app.include_router(
        categories,
        prefix="/api/v1/categories",
        tags=["Categories"],
    )
    app.include_router(
        transactions,
        prefix="/api/v1/transactions",
        tags=["Transactions"],
    )


__all__ = ["include_routers"]
