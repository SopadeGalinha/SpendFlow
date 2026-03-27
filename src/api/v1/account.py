import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.v1.deps import get_current_user
from src.database import get_session
from src.models import User
from src.schemas import AccountCreate, AccountResponse, AccountUpdate
from src.services import AccountService

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("", response_model=list[AccountResponse])
async def list_accounts(
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return await AccountService.get_active_accounts(db, current_user.id)


@router.get("/{account_id}", response_model=AccountResponse)
async def get_account(
    account_id: UUID,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    account = await AccountService.get_owned_account(
        db,
        current_user.id,
        account_id,
    )
    if account is None:
        raise HTTPException(status_code=404, detail="Account not found")
    return account


@router.post(
    "",
    response_model=AccountResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_account(
    account_in: AccountCreate,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return await AccountService.create_account(
        db,
        current_user.id,
        account_in,
    )


@router.put("/{account_id}", response_model=AccountResponse)
async def update_account(
    account_id: UUID,
    account_in: AccountUpdate,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return await AccountService.update_account(
        db,
        current_user.id,
        account_id,
        account_in,
    )


@router.delete(
    "/{account_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_account(
    account_id: UUID,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    await AccountService.soft_delete_account(db, current_user.id, account_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{account_id}/restore", response_model=AccountResponse)
async def restore_account(
    account_id: UUID,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return await AccountService.restore_account(
        db,
        current_user.id,
        account_id,
    )
