
import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import get_session
from src.services import AccountService
from src.api.v1.deps import get_current_user
from src.models import User, Account


router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/accounts/{account_id}/restore")
async def restore_account(
    account_id: UUID,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    Restore a previously soft-deleted account (set deleted_at to None)
    if owned by the current user.
    """
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
