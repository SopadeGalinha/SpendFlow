from fastapi import FastAPI

from src.api.v1 import accounts, auth, calendar


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
        auth,
        prefix="/api/v1/auth",
        tags=["Authentication"],
    )


__all__ = ["include_routers"]
