import logging
from datetime import date, datetime, timezone
from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import Transaction, TransactionType
from src.repositories import CategoryRepository, TransactionRepository
from src.schemas import TransactionCreate, TransactionUpdate
from src.services.category import CategoryService

logger = logging.getLogger(__name__)


class TransactionService:
    @staticmethod
    def _validate_positive_amount(amount: Decimal) -> Decimal:
        if amount <= Decimal("0.00"):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="Transaction amount must be greater than zero.",
            )
        return amount

    @staticmethod
    async def _get_valid_category(
        db: AsyncSession,
        user_id: UUID,
        category_id: UUID | None,
        transaction_type: TransactionType,
    ) -> UUID | None:
        if category_id is None:
            return None

        await CategoryService.ensure_default_catalog(db, user_id)
        category = await CategoryRepository.get_accessible_category(
            db,
            user_id,
            category_id,
        )
        if category is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found.",
            )
        if category.type != transaction_type:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Category type must match the transaction type.",
            )
        return category.id

    @staticmethod
    def _signed_amount(
        amount: Decimal,
        transaction_type: TransactionType,
    ) -> Decimal:
        if transaction_type == TransactionType.INCOME:
            return amount
        return -amount

    @classmethod
    def _apply_balance_delta(
        cls,
        current_balance: Decimal,
        amount: Decimal,
        transaction_type: TransactionType,
    ) -> Decimal:
        next_balance = current_balance + cls._signed_amount(
            amount,
            transaction_type,
        )
        if next_balance < Decimal("0.00"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Transaction would make the account balance negative.",
            )
        return next_balance

    @classmethod
    async def create_transaction(
        cls,
        db: AsyncSession,
        user_id: UUID,
        transaction_data: TransactionCreate,
    ) -> Transaction:
        account = await TransactionRepository.get_owned_account(
            db,
            user_id,
            transaction_data.account_id,
        )
        if account is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Account not found.",
            )

        amount = cls._validate_positive_amount(transaction_data.amount)

        account.balance = cls._apply_balance_delta(
            account.balance,
            amount,
            transaction_data.type,
        )
        category_id = await cls._get_valid_category(
            db,
            user_id,
            transaction_data.category_id,
            transaction_data.type,
        )

        transaction = Transaction(
            description=transaction_data.description,
            amount=amount,
            type=transaction_data.type,
            transaction_date=transaction_data.transaction_date,
            account_id=transaction_data.account_id,
            category_id=category_id,
        )
        db.add(account)
        created_transaction = await TransactionRepository.create(
            db,
            transaction,
        )
        logger.info(
            "Transaction created",
            extra={
                "transaction_id": str(created_transaction.id),
                "account_id": str(created_transaction.account_id),
                "type": created_transaction.type.value,
            },
        )
        return created_transaction

    @staticmethod
    async def get_transaction(
        db: AsyncSession,
        user_id: UUID,
        transaction_id: UUID,
    ) -> Transaction:
        transaction = await TransactionRepository.get_owned_transaction(
            db,
            user_id,
            transaction_id,
        )
        if transaction is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transaction not found.",
            )
        return transaction

    @staticmethod
    async def list_transactions(
        db: AsyncSession,
        user_id: UUID,
        account_id: UUID | None = None,
        category_id: UUID | None = None,
        transaction_type: TransactionType | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> list[Transaction]:
        if account_id is not None:
            account = await TransactionRepository.get_owned_account(
                db,
                user_id,
                account_id,
            )
            if account is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Account not found.",
                )

        if category_id is not None:
            await CategoryService.ensure_default_catalog(db, user_id)
            category = await CategoryRepository.get_accessible_category(
                db,
                user_id,
                category_id,
            )
            if category is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Category not found.",
                )

        return await TransactionRepository.list_owned_transactions(
            db,
            user_id,
            account_id=account_id,
            category_id=category_id,
            transaction_type=transaction_type,
            date_from=date_from,
            date_to=date_to,
        )

    @classmethod
    async def update_transaction(
        cls,
        db: AsyncSession,
        user_id: UUID,
        transaction_id: UUID,
        transaction_data: TransactionUpdate,
    ) -> Transaction:
        transaction = await cls.get_transaction(db, user_id, transaction_id)
        account = await TransactionRepository.get_owned_account(
            db,
            user_id,
            transaction.account_id,
        )
        if account is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Account not found.",
            )

        restored_balance = account.balance - cls._signed_amount(
            transaction.amount,
            transaction.type,
        )
        new_amount = (
            cls._validate_positive_amount(transaction_data.amount)
            if transaction_data.amount is not None
            else transaction.amount
        )
        new_type = transaction_data.type or transaction.type
        category_id_updated = (
            "category_id" in transaction_data.model_fields_set
        )
        new_category_id = (
            transaction_data.category_id
            if category_id_updated
            else transaction.category_id
        )
        validated_category_id = await cls._get_valid_category(
            db,
            user_id,
            new_category_id,
            new_type,
        )
        account.balance = cls._apply_balance_delta(
            restored_balance,
            new_amount,
            new_type,
        )

        if transaction_data.description is not None:
            transaction.description = transaction_data.description
        if transaction_data.amount is not None:
            transaction.amount = transaction_data.amount
        if transaction_data.transaction_date is not None:
            transaction.transaction_date = transaction_data.transaction_date
        if transaction_data.type is not None:
            transaction.type = transaction_data.type
        if category_id_updated:
            transaction.category_id = validated_category_id

        db.add(account)
        updated_transaction = await TransactionRepository.save(db, transaction)
        logger.info(
            "Transaction updated",
            extra={"transaction_id": str(updated_transaction.id)},
        )
        return updated_transaction

    @classmethod
    async def delete_transaction(
        cls,
        db: AsyncSession,
        user_id: UUID,
        transaction_id: UUID,
    ) -> None:
        transaction = await cls.get_transaction(db, user_id, transaction_id)
        account = await TransactionRepository.get_owned_account(
            db,
            user_id,
            transaction.account_id,
        )
        if account is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Account not found.",
            )

        account.balance -= cls._signed_amount(
            transaction.amount,
            transaction.type,
        )
        transaction.deleted_at = datetime.now(timezone.utc)
        db.add(account)
        await TransactionRepository.save(db, transaction)
        logger.info(
            "Transaction soft-deleted",
            extra={"transaction_id": str(transaction.id)},
        )
