
import logging
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import get_session
from src.services import AccountService
from src.api.v1.deps import get_current_user
from src.models import User, Account
from src.schemas import AccountCreate, AccountUpdate, AccountResponse


router = APIRouter()
logger = logging.getLogger(__name__)


# List all accounts for the authenticated user
@router.get("/accounts", response_model=list[AccountResponse])
async def list_accounts(
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    accounts = await AccountService.get_active_accounts(db, current_user.id)
    return accounts


# Get a single account by id (must belong to user)
@router.get("/accounts/{account_id}", response_model=AccountResponse)
async def get_account(
    account_id: UUID,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    account = await db.get(Account, account_id)
    if (
        not account
        or account.user_id != current_user.id
        or account.deleted_at is not None
    ):
        raise HTTPException(status_code=404, detail="Account not found")
    return account


# Create a new account
@router.post(
    "/accounts",
    response_model=AccountResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_account(
    account_in: AccountCreate,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    from decimal import Decimal
    account = Account(
        name=account_in.name,
        balance=(
            account_in.balance
            if account_in.balance is not None
            else Decimal("0.00")
        ),
        user_id=current_user.id,
    )
    db.add(account)
    await db.commit()
    await db.refresh(account)
    return account


# Update an existing account
@router.put("/accounts/{account_id}", response_model=AccountResponse)
async def update_account(
    account_id: UUID,
    account_in: AccountUpdate,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    account = await db.get(Account, account_id)
    if (
        not account
        or account.user_id != current_user.id
        or account.deleted_at is not None
    ):
        raise HTTPException(status_code=404, detail="Account not found")
    if account_in.name is not None:
        account.name = account_in.name
    if account_in.balance is not None:
        account.balance = account_in.balance
    db.add(account)
    await db.commit()
    await db.refresh(account)
    return account


# Soft delete an account
@router.delete(
    "/accounts/{account_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_account(
    account_id: UUID,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    account = await db.get(Account, account_id)
    if (
        not account
        or account.user_id != current_user.id
        or account.deleted_at is not None
    ):
        raise HTTPException(status_code=404, detail="Account not found")
    from datetime import datetime, timezone
    account.deleted_at = datetime.now(timezone.utc)
    db.add(account)
    await db.commit()
    return


# Restore a soft-deleted account
@router.post("/accounts/{account_id}/restore")
async def restore_account(
    account_id: UUID,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    account = await db.get(Account, account_id)
    if (
        not account
        or account.user_id != current_user.id
        or account.deleted_at is None
    ):
        logger.warning(
            f"Unauthorized or invalid restore attempt for account {account_id}"
        )
        raise HTTPException(
            status_code=403,
            detail="Account not found, not owned by user, or not deleted."
        )
    from src.services import AccountService
    success = await AccountService.restore_account(db, account_id)
    if not success:
        logger.warning(
            f"Attempt to restore non-existent or not deleted account "
            f"{account_id}"
        )
        raise HTTPException(
            status_code=400,
            detail="Could not restore account",
        )
    return {"message": "Account restored"}
