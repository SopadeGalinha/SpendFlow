from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import Account, RecurringRule


class RecurringRuleRepository:
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
    async def get_owned_rule(
        db: AsyncSession,
        user_id: UUID,
        rule_id: UUID,
    ) -> RecurringRule | None:
        stmt = (
            select(RecurringRule)
            .join(Account, RecurringRule.account_id == Account.id)
            .where(
                RecurringRule.id == rule_id,
                RecurringRule.deleted_at.is_(None),
                Account.user_id == user_id,
                Account.deleted_at.is_(None),
            )
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def list_owned_rules(
        db: AsyncSession,
        user_id: UUID,
        account_id: UUID | None = None,
    ) -> list[RecurringRule]:
        stmt = (
            select(RecurringRule)
            .join(Account, RecurringRule.account_id == Account.id)
            .where(
                RecurringRule.deleted_at.is_(None),
                Account.user_id == user_id,
                Account.deleted_at.is_(None),
            )
            .order_by(
                RecurringRule.start_date.asc(),
                RecurringRule.description.asc(),
            )
        )

        if account_id is not None:
            stmt = stmt.where(RecurringRule.account_id == account_id)

        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def create(
        db: AsyncSession,
        rule: RecurringRule,
    ) -> RecurringRule:
        db.add(rule)
        await db.flush()
        return rule

    @staticmethod
    async def save(
        db: AsyncSession,
        rule: RecurringRule,
    ) -> RecurringRule:
        db.add(rule)
        await db.flush()
        return rule
