from datetime import date
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import Account, Transaction, TransactionType


class TransactionRepository:
    @staticmethod
    async def get_owned_account(
        db: AsyncSession,
        user_id: UUID,
        account_id: UUID,
    ) -> Account | None:
        stmt = select(Account).where(
            Account.id == account_id,
            Account.user_id == user_id,
            Account.deleted_at.is_(None),
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_owned_transaction(
        db: AsyncSession,
        user_id: UUID,
        transaction_id: UUID,
    ) -> Transaction | None:
        stmt = (
            select(Transaction)
            .join(Account, Transaction.account_id == Account.id)
            .where(
                Transaction.id == transaction_id,
                Transaction.deleted_at.is_(None),
                Account.user_id == user_id,
                Account.deleted_at.is_(None),
            )
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def list_owned_transactions(
        db: AsyncSession,
        user_id: UUID,
        account_id: UUID | None = None,
        category_id: UUID | None = None,
        transaction_type: TransactionType | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> list[Transaction]:
        stmt = (
            select(Transaction)
            .join(Account, Transaction.account_id == Account.id)
            .where(
                Transaction.deleted_at.is_(None),
                Account.user_id == user_id,
                Account.deleted_at.is_(None),
            )
        )

        if account_id is not None:
            stmt = stmt.where(Transaction.account_id == account_id)
        if category_id is not None:
            stmt = stmt.where(Transaction.category_id == category_id)
        if transaction_type is not None:
            stmt = stmt.where(Transaction.type == transaction_type)
        if date_from is not None:
            stmt = stmt.where(Transaction.transaction_date >= date_from)
        if date_to is not None:
            stmt = stmt.where(Transaction.transaction_date <= date_to)

        stmt = stmt.order_by(
            Transaction.transaction_date.desc(),
            Transaction.created_at.desc(),
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def create(
        db: AsyncSession,
        transaction: Transaction,
    ) -> Transaction:
        db.add(transaction)
        await db.flush()
        return transaction

    @staticmethod
    async def save(db: AsyncSession, transaction: Transaction) -> Transaction:
        db.add(transaction)
        await db.flush()
        return transaction
