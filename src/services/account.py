import logging
from datetime import date, datetime, timezone
from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import Account, Transaction, TransactionKind, TransactionType
from src.schemas import AccountCreate, AccountUpdate

logger = logging.getLogger(__name__)


class AccountService:
    @staticmethod
    async def get_active_accounts(
        db: AsyncSession,
        user_id: UUID,
    ) -> list[Account]:
        stmt = select(Account).where(
            Account.user_id == user_id,
            Account.deleted_at.is_(None),
        )
        stmt = stmt.order_by(Account.name.asc(), Account.id.asc())
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def get_owned_account(
        db: AsyncSession,
        user_id: UUID,
        account_id: UUID,
        include_deleted: bool = False,
    ) -> Account | None:
        stmt = select(Account).where(
            Account.id == account_id,
            Account.user_id == user_id,
        )
        if not include_deleted:
            stmt = stmt.where(Account.deleted_at.is_(None))
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @classmethod
    async def create_account(
        cls,
        db: AsyncSession,
        user_id: UUID,
        account_in: AccountCreate,
    ) -> Account:
        opening_balance = account_in.opening_balance or Decimal("0.00")
        account = Account(
            name=account_in.name,
            account_type=account_in.account_type,
            balance=Decimal("0.00"),
            user_id=user_id,
        )
        db.add(account)
        await db.flush()

        if opening_balance > Decimal("0.00"):
            account.balance = opening_balance
            db.add(
                Transaction(
                    description="Opening balance",
                    amount=opening_balance,
                    type=TransactionType.INCOME,
                    kind=TransactionKind.OPENING_BALANCE,
                    transaction_date=date.today(),
                    account_id=account.id,
                )
            )

        await db.commit()
        await db.refresh(account)
        return account

    @classmethod
    async def update_account(
        cls,
        db: AsyncSession,
        user_id: UUID,
        account_id: UUID,
        account_in: AccountUpdate,
    ) -> Account:
        account = await cls.get_owned_account(db, user_id, account_id)
        if account is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Account not found.",
            )

        if account_in.name is not None:
            account.name = account_in.name
        if account_in.account_type is not None:
            account.account_type = account_in.account_type

        db.add(account)
        await db.commit()
        await db.refresh(account)
        return account

    @classmethod
    async def soft_delete_account(
        cls,
        db: AsyncSession,
        user_id: UUID,
        account_id: UUID,
    ) -> None:
        account = await cls.get_owned_account(db, user_id, account_id)
        if account is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Account not found.",
            )

        account.deleted_at = datetime.now(timezone.utc)
        db.add(account)
        await db.commit()
        await db.refresh(account)

        logger.info(f"Account {account_id} soft-deleted")

    @classmethod
    async def restore_account(
        cls,
        db: AsyncSession,
        user_id: UUID,
        account_id: UUID,
    ) -> Account:
        account = await cls.get_owned_account(
            db,
            user_id,
            account_id,
            include_deleted=True,
        )
        if account is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Account not found.",
            )
        if account.deleted_at is None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Account is already active.",
            )

        account.deleted_at = None
        db.add(account)
        await db.commit()
        await db.refresh(account)

        logger.info(f"Account {account_id} restored")
        return account
