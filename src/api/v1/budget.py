from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.v1.deps import get_current_user
from src.database import get_session
from src.models import BudgetStatus, User
from src.schemas import (
    BudgetCloneCreate,
    BudgetCreate,
    BudgetResponse,
    BudgetUpdate,
)
from src.services import BudgetService

router = APIRouter()


@router.post(
    "",
    response_model=BudgetResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_budget(
    budget_in: BudgetCreate,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return await BudgetService.create_budget(db, current_user.id, budget_in)


@router.get("", response_model=list[BudgetResponse])
async def list_budgets(
    status_filter: BudgetStatus | None = Query(default=None, alias="status"),
    year: int | None = Query(default=None, ge=1900, le=9999),
    month: int | None = Query(default=None, ge=1, le=12),
    period_start_from: date | None = None,
    period_end_to: date | None = None,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return await BudgetService.list_budgets(
        db,
        current_user.id,
        status_filter=status_filter,
        year=year,
        month=month,
        period_start_from=period_start_from,
        period_end_to=period_end_to,
    )


@router.get("/{budget_id}", response_model=BudgetResponse)
async def get_budget(
    budget_id: UUID,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return await BudgetService.get_budget(db, current_user.id, budget_id)


@router.put("/{budget_id}", response_model=BudgetResponse)
async def update_budget(
    budget_id: UUID,
    budget_in: BudgetUpdate,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return await BudgetService.update_budget(
        db,
        current_user.id,
        budget_id,
        budget_in,
    )


@router.post(
    "/{budget_id}/clone",
    response_model=BudgetResponse,
    status_code=status.HTTP_201_CREATED,
)
async def clone_budget(
    budget_id: UUID,
    clone_in: BudgetCloneCreate,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return await BudgetService.clone_budget(
        db,
        current_user.id,
        budget_id,
        clone_in,
    )


@router.delete("/{budget_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_budget(
    budget_id: UUID,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    await BudgetService.delete_budget(db, current_user.id, budget_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
