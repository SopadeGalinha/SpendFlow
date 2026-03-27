import logging
from datetime import date, datetime, timezone
from decimal import Decimal
from uuid import UUID, uuid4

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import (
    CategoryType,
    Transaction,
    TransactionKind,
    TransactionType,
)
from src.repositories import CategoryRepository, TransactionRepository
from src.schemas import (
    TransactionAdjustmentCreate,
    TransactionCreate,
    TransactionUpdate,
    TransferCreate,
)

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
        category_type: CategoryType,
    ) -> UUID | None:
        if category_id is None:
            return None

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
        if category.type != category_type:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="Category type must match the transaction type.",
            )
        return category.id

    @staticmethod
    async def _get_default_transfer_category_id(
        db: AsyncSession,
        user_id: UUID,
        category_id: UUID | None,
    ) -> UUID:
        validated_category_id = await TransactionService._get_valid_category(
            db,
            user_id,
            category_id,
            CategoryType.TRANSFER,
        )
        if validated_category_id is not None:
            return validated_category_id

        category = (
            await CategoryRepository.find_system_category_by_type_and_slug(
                db,
                CategoryType.TRANSFER,
                "transfer",
            )
        )
        if category is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Transfer category not configured.",
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
                status_code=status.HTTP_409_CONFLICT,
                detail="Transaction would make the account balance negative.",
            )
        return next_balance

    @classmethod
    async def _create_entry(
        cls,
        db: AsyncSession,
        account,
        *,
        description: str,
        amount: Decimal,
        transaction_type: TransactionType,
        kind: TransactionKind,
        transaction_date: date,
        category_id: UUID | None = None,
        transfer_group_id: UUID | None = None,
    ) -> Transaction:
        account.balance = cls._apply_balance_delta(
            account.balance,
            amount,
            transaction_type,
        )
        db.add(account)
        transaction = Transaction(
            description=description,
            amount=amount,
            type=transaction_type,
            kind=kind,
            transaction_date=transaction_date,
            account_id=account.id,
            category_id=category_id,
            transfer_group_id=transfer_group_id,
        )
        return await TransactionRepository.create(db, transaction)

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
        category_id = await cls._get_valid_category(
            db,
            user_id,
            transaction_data.category_id,
            CategoryType(transaction_data.type.value),
        )
        created_transaction = await cls._create_entry(
            db,
            account,
            description=transaction_data.description,
            amount=amount,
            transaction_type=transaction_data.type,
            kind=TransactionKind.REGULAR,
            transaction_date=transaction_data.transaction_date,
            category_id=category_id,
        )
        await db.commit()
        await db.refresh(created_transaction)
        logger.info(
            "Transaction created",
            extra={
                "transaction_id": str(created_transaction.id),
                "account_id": str(created_transaction.account_id),
                "type": created_transaction.type.value,
            },
        )
        return created_transaction

    @classmethod
    async def create_adjustment(
        cls,
        db: AsyncSession,
        user_id: UUID,
        transaction_data: TransactionAdjustmentCreate,
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
        category_id = await cls._get_valid_category(
            db,
            user_id,
            transaction_data.category_id,
            CategoryType(transaction_data.type.value),
        )
        created_transaction = await cls._create_entry(
            db,
            account,
            description=transaction_data.description,
            amount=amount,
            transaction_type=transaction_data.type,
            kind=TransactionKind.ADJUSTMENT,
            transaction_date=transaction_data.transaction_date,
            category_id=category_id,
        )
        await db.commit()
        await db.refresh(created_transaction)
        return created_transaction

    @classmethod
    async def create_transfer(
        cls,
        db: AsyncSession,
        user_id: UUID,
        transfer_data: TransferCreate,
    ) -> tuple[UUID, Transaction, Transaction]:
        if transfer_data.from_account_id == transfer_data.to_account_id:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="Transfer accounts must be different.",
            )

        source_account = await TransactionRepository.get_owned_account(
            db,
            user_id,
            transfer_data.from_account_id,
        )
        destination_account = await TransactionRepository.get_owned_account(
            db,
            user_id,
            transfer_data.to_account_id,
        )
        if source_account is None or destination_account is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="One or more accounts were not found.",
            )

        amount = cls._validate_positive_amount(transfer_data.amount)
        category_id = await cls._get_default_transfer_category_id(
            db,
            user_id,
            transfer_data.category_id,
        )
        transfer_group_id = uuid4()

        from_entry = await cls._create_entry(
            db,
            source_account,
            description=transfer_data.description,
            amount=amount,
            transaction_type=TransactionType.EXPENSE,
            kind=TransactionKind.TRANSFER,
            transaction_date=transfer_data.transaction_date,
            category_id=category_id,
            transfer_group_id=transfer_group_id,
        )
        to_entry = await cls._create_entry(
            db,
            destination_account,
            description=transfer_data.description,
            amount=amount,
            transaction_type=TransactionType.INCOME,
            kind=TransactionKind.TRANSFER,
            transaction_date=transfer_data.transaction_date,
            category_id=category_id,
            transfer_group_id=transfer_group_id,
        )

        await db.commit()
        await db.refresh(from_entry)
        await db.refresh(to_entry)
        return transfer_group_id, from_entry, to_entry

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
        if transaction.kind in {
            TransactionKind.OPENING_BALANCE,
            TransactionKind.TRANSFER,
        }:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This transaction cannot be updated directly.",
            )

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
            CategoryType(new_type.value),
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
        await db.commit()
        await db.refresh(updated_transaction)
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
        if transaction.kind in {
            TransactionKind.OPENING_BALANCE,
            TransactionKind.TRANSFER,
        }:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This transaction cannot be deleted directly.",
            )

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
        await db.commit()
        logger.info(
            "Transaction soft-deleted",
            extra={"transaction_id": str(transaction.id)},
        )
