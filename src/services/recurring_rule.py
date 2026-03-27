import logging
from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import RecurringRule
from src.repositories import RecurringRuleRepository
from src.schemas import RecurringRuleCreate, RecurringRuleUpdate

logger = logging.getLogger(__name__)


class RecurringRuleService:
    @staticmethod
    def _validate_positive_amount(amount: Decimal) -> Decimal:
        if amount <= Decimal("0.00"):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="Recurring rule amount must be greater than zero.",
            )
        return amount

    @staticmethod
    def _validate_interval(interval: int) -> int:
        if interval < 1:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="Recurring rule interval must be at least 1.",
            )
        return interval

    @classmethod
    def _validate_date_range(
        cls,
        start_date,
        end_date,
    ) -> None:
        if end_date is not None and end_date < start_date:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="end_date must be on or after start_date.",
            )

    @classmethod
    async def create_rule(
        cls,
        db: AsyncSession,
        user_id: UUID,
        rule_in: RecurringRuleCreate,
    ) -> RecurringRule:
        account = await RecurringRuleRepository.get_owned_account(
            db,
            user_id,
            rule_in.account_id,
        )
        if account is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Account not found.",
            )

        cls._validate_date_range(rule_in.start_date, rule_in.end_date)
        amount = cls._validate_positive_amount(rule_in.amount)
        interval = cls._validate_interval(rule_in.interval)

        rule = RecurringRule(
            description=rule_in.description,
            amount=amount,
            type=rule_in.type,
            frequency=rule_in.frequency,
            interval=interval,
            start_date=rule_in.start_date,
            end_date=rule_in.end_date,
            weekend_adjustment=rule_in.weekend_adjustment,
            account_id=rule_in.account_id,
        )
        created_rule = await RecurringRuleRepository.create(db, rule)
        await db.commit()
        await db.refresh(created_rule)
        logger.info(
            "Recurring rule created",
            extra={
                "rule_id": str(created_rule.id),
                "account_id": str(created_rule.account_id),
                "type": created_rule.type.value,
                "frequency": created_rule.frequency.value,
            },
        )
        return created_rule

    @staticmethod
    async def list_rules(
        db: AsyncSession,
        user_id: UUID,
        account_id: UUID | None = None,
    ) -> list[RecurringRule]:
        if account_id is not None:
            account = await RecurringRuleRepository.get_owned_account(
                db,
                user_id,
                account_id,
            )
            if account is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Account not found.",
                )

        return await RecurringRuleRepository.list_owned_rules(
            db,
            user_id,
            account_id=account_id,
        )

    @staticmethod
    async def get_rule(
        db: AsyncSession,
        user_id: UUID,
        rule_id: UUID,
    ) -> RecurringRule:
        rule = await RecurringRuleRepository.get_owned_rule(
            db,
            user_id,
            rule_id,
        )
        if rule is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Recurring rule not found.",
            )
        return rule

    @classmethod
    async def update_rule(
        cls,
        db: AsyncSession,
        user_id: UUID,
        rule_id: UUID,
        rule_in: RecurringRuleUpdate,
    ) -> RecurringRule:
        rule = await cls.get_rule(db, user_id, rule_id)

        new_start_date = rule_in.start_date or rule.start_date
        end_date_updated = "end_date" in rule_in.model_fields_set
        new_end_date = rule_in.end_date if end_date_updated else rule.end_date
        cls._validate_date_range(new_start_date, new_end_date)

        if rule_in.description is not None:
            rule.description = rule_in.description
        if rule_in.amount is not None:
            rule.amount = cls._validate_positive_amount(rule_in.amount)
        if rule_in.type is not None:
            rule.type = rule_in.type
        if rule_in.frequency is not None:
            rule.frequency = rule_in.frequency
        if rule_in.interval is not None:
            rule.interval = cls._validate_interval(rule_in.interval)
        if rule_in.start_date is not None:
            rule.start_date = rule_in.start_date
        if end_date_updated:
            rule.end_date = rule_in.end_date
        if rule_in.weekend_adjustment is not None:
            rule.weekend_adjustment = rule_in.weekend_adjustment

        updated_rule = await RecurringRuleRepository.save(db, rule)
        await db.commit()
        await db.refresh(updated_rule)
        logger.info(
            "Recurring rule updated",
            extra={"rule_id": str(updated_rule.id)},
        )
        return updated_rule

    @classmethod
    async def delete_rule(
        cls,
        db: AsyncSession,
        user_id: UUID,
        rule_id: UUID,
    ) -> None:
        rule = await cls.get_rule(db, user_id, rule_id)
        rule.deleted_at = datetime.now(timezone.utc)
        await RecurringRuleRepository.save(db, rule)
        await db.commit()
        logger.info(
            "Recurring rule soft-deleted",
            extra={"rule_id": str(rule.id)},
        )
