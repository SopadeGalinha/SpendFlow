import calendar as py_calendar
from datetime import date
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.api.v1.deps import get_current_user
from src.database import get_session
from src.models import RecurringRule, User
from src.schemas.finance import ProjectionResponse
from src.services.calendar import CalendarService

router = APIRouter()


@router.get("/projection", response_model=List[ProjectionResponse])
async def get_calendar_projection(
    account_id: UUID,
    month: int = Query(..., ge=1, le=12),
    year: int = Query(..., ge=2024),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    Get a projection of recurring transactions for a given account and
    month/year.
    Only returns projections for accounts owned by the current user.
    """
    last_day = py_calendar.monthrange(year, month)[1]
    start_date = date(year, month, 1)
    end_date = date(year, month, last_day)

    from src.models import Account

    # Only fetch non-deleted account
    account_stmt = select(Account).where(
        Account.id == account_id,
        Account.deleted_at.is_(None),
    )
    account_result = await session.execute(account_stmt)
    account = account_result.scalar_one_or_none()
    if not account or account.user_id != current_user.id:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=403,
            detail="Account does not belong to the current user.",
        )

    # Fetch recurring rules for the account from the database, only non-deleted
    statement = select(RecurringRule).where(
        RecurringRule.account_id == account_id,
        RecurringRule.deleted_at.is_(None),
    )
    result = await session.execute(statement)
    rules = result.scalars().all()

    if not rules:
        return []

    # 4. Chama o serviço de projeção (o cérebro do app)
    projections = CalendarService.get_projection(
        rules=rules,
        start_period=start_date,
        end_period=end_date,
        current_balance=account.balance,
    )

    return projections
