from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.v1.deps import get_current_user
from src.database import get_session
from src.models import TransactionType, User
from src.schemas import (
    TransactionAdjustmentCreate,
    TransactionCreate,
    TransactionResponse,
    TransactionUpdate,
    TransferCreate,
    TransferResponse,
)
from src.services import TransactionService

router = APIRouter()


@router.post("", response_model=TransactionResponse, status_code=201)
async def create_transaction(
    transaction_in: TransactionCreate,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return await TransactionService.create_transaction(
        db,
        current_user.id,
        transaction_in,
    )


@router.post(
    "/adjustments",
    response_model=TransactionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_adjustment(
    transaction_in: TransactionAdjustmentCreate,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return await TransactionService.create_adjustment(
        db,
        current_user.id,
        transaction_in,
    )


@router.post(
    "/transfers",
    response_model=TransferResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_transfer(
    transfer_in: TransferCreate,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    transfer_group_id, from_entry, to_entry = (
        await TransactionService.create_transfer(
            db,
            current_user.id,
            transfer_in,
        )
    )
    return TransferResponse(
        transfer_group_id=transfer_group_id,
        amount=transfer_in.amount,
        transaction_date=transfer_in.transaction_date,
        from_entry=from_entry,
        to_entry=to_entry,
    )


@router.get("", response_model=list[TransactionResponse])
async def list_transactions(
    account_id: UUID | None = None,
    category_id: UUID | None = None,
    transaction_type: TransactionType | None = Query(None, alias="type"),
    date_from: date | None = None,
    date_to: date | None = None,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return await TransactionService.list_transactions(
        db,
        current_user.id,
        account_id=account_id,
        category_id=category_id,
        transaction_type=transaction_type,
        date_from=date_from,
        date_to=date_to,
    )


@router.get("/{transaction_id}", response_model=TransactionResponse)
async def get_transaction(
    transaction_id: UUID,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return await TransactionService.get_transaction(
        db,
        current_user.id,
        transaction_id,
    )


@router.put("/{transaction_id}", response_model=TransactionResponse)
async def update_transaction(
    transaction_id: UUID,
    transaction_in: TransactionUpdate,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return await TransactionService.update_transaction(
        db,
        current_user.id,
        transaction_id,
        transaction_in,
    )


@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_transaction(
    transaction_id: UUID,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    await TransactionService.delete_transaction(
        db,
        current_user.id,
        transaction_id,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
