import logging
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import Account

logger = logging.getLogger(__name__)


class AccountService:
    @staticmethod
    async def get_active_accounts(db: AsyncSession, user_id: UUID):
        """Retrieve all active accounts not soft-deleted."""
        stmt = select(Account).where(
            Account.user_id == user_id,
            Account.deleted_at.is_(None),
        )
        result = await db.execute(stmt)
        accounts = result.scalars().all()
        return [
            {
                "id": str(acc.id),
                "name": acc.name,
                "balance": str(acc.balance),
            }
            for acc in accounts
        ]

    @staticmethod
    async def soft_delete_account(db: AsyncSession, account_id: UUID) -> bool:
        """Mark an account as deleted (soft delete)."""
        stmt = select(Account).where(
            Account.id == account_id,
            Account.deleted_at.is_(None),
        )
        result = await db.execute(stmt)
        account = result.scalar_one_or_none()

        if not account:
            return False

        account.deleted_at = datetime.now(timezone.utc)
        db.add(account)
        await db.commit()
        await db.refresh(account)

        logger.info(f"Account {account_id} soft-deleted")
        return True

    @staticmethod
    async def restore_account(db: AsyncSession, account_id: UUID) -> bool:
        """Restore a soft-deleted account (set deleted_at back to None)."""
        stmt = select(Account).where(
            Account.id == account_id,
            Account.deleted_at.is_not(None),
        )
        result = await db.execute(stmt)
        account = result.scalar_one_or_none()

        if not account:
            return False

        account.deleted_at = None
        db.add(account)
        await db.commit()

        logger.info(f"Account {account_id} restored")
        return True
