from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.v1.deps import get_current_user
from src.database import get_session
from src.models import User
from src.schemas import (
    RecurringRuleCreate,
    RecurringRuleResponse,
    RecurringRuleUpdate,
)
from src.services import RecurringRuleService

router = APIRouter()


@router.post(
    "/rules",
    response_model=RecurringRuleResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_recurring_rule(
    rule_in: RecurringRuleCreate,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return await RecurringRuleService.create_rule(
        db,
        current_user.id,
        rule_in,
    )


@router.get("/rules", response_model=list[RecurringRuleResponse])
async def list_recurring_rules(
    account_id: UUID | None = Query(None),
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return await RecurringRuleService.list_rules(
        db,
        current_user.id,
        account_id=account_id,
    )


@router.get("/rules/{rule_id}", response_model=RecurringRuleResponse)
async def get_recurring_rule(
    rule_id: UUID,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return await RecurringRuleService.get_rule(
        db,
        current_user.id,
        rule_id,
    )


@router.put("/rules/{rule_id}", response_model=RecurringRuleResponse)
async def update_recurring_rule(
    rule_id: UUID,
    rule_in: RecurringRuleUpdate,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return await RecurringRuleService.update_rule(
        db,
        current_user.id,
        rule_id,
        rule_in,
    )


@router.delete("/rules/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_recurring_rule(
    rule_id: UUID,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    await RecurringRuleService.delete_rule(
        db,
        current_user.id,
        rule_id,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
