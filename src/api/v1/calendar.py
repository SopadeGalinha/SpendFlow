from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from datetime import date
import calendar as py_calendar
from typing import List
from uuid import UUID

from src.database import get_session
from src.models.finance import RecurringRule
from src.services.calendar_service import CalendarService
from src.schemas.finance import ProjectionResponse

router = APIRouter()


@router.get("/projection", response_model=List[ProjectionResponse])
async def get_calendar_projection(
    account_id: UUID,
    month: int = Query(..., ge=1, le=12),
    year: int = Query(..., ge=2024),
    session: AsyncSession = Depends(get_session),
):
    # 1. Calcula o intervalo do mês
    last_day = py_calendar.monthrange(year, month)[1]
    start_date = date(year, month, 1)
    end_date = date(year, month, last_day)

    # 2. Busca as regras recorrentes da conta no banco
    statement = select(RecurringRule).where(
        RecurringRule.account_id == account_id)
    result = await session.execute(statement)
    rules = result.scalars().all()

    if not rules:
        return []

    # 3. Chama o serviço de projeção (o cérebro do app)
    projections = CalendarService.get_projection(
        rules=rules, start_period=start_date, end_period=end_date
    )

    return projections
