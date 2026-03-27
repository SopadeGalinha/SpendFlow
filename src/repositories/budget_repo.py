from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import (
    Budget,
    BudgetScope,
    Category,
    CategoryGroup,
    Transaction,
    TransactionKind,
    TransactionType,
)


class BudgetRepository:
    @staticmethod
    async def load_target_metadata(
        db: AsyncSession,
        budgets: list[Budget],
    ) -> tuple[
        dict[UUID, Category],
        dict[UUID, CategoryGroup],
    ]:
        category_ids = {
            budget.category_id
            for budget in budgets
            if budget.category_id is not None
        }
        group_ids = {
            budget.category_group_id
            for budget in budgets
            if budget.category_group_id is not None
        }

        categories_by_id: dict[UUID, Category] = {}
        if category_ids:
            category_stmt = select(Category).where(
                Category.id.in_(category_ids)
            )
            category_result = await db.execute(category_stmt)
            categories = list(category_result.scalars().all())
            categories_by_id = {
                category.id: category for category in categories
            }
            group_ids.update(category.group_id for category in categories)

        groups_by_id: dict[UUID, CategoryGroup] = {}
        if group_ids:
            group_stmt = select(CategoryGroup).where(
                CategoryGroup.id.in_(group_ids)
            )
            group_result = await db.execute(group_stmt)
            groups = list(group_result.scalars().all())
            groups_by_id = {group.id: group for group in groups}

        return categories_by_id, groups_by_id

    @staticmethod
    async def get_owned_budget(
        db: AsyncSession,
        user_id: UUID,
        budget_id: UUID,
    ) -> Budget | None:
        stmt = select(Budget).where(
            Budget.id == budget_id,
            Budget.user_id == user_id,
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def list_owned_budgets(
        db: AsyncSession,
        user_id: UUID,
        *,
        today: date | None = None,
        status_filter: str | None = None,
        overlap_start: date | None = None,
        overlap_end: date | None = None,
        period_start_from: date | None = None,
        period_end_to: date | None = None,
    ) -> list[Budget]:
        stmt = select(Budget).where(Budget.user_id == user_id)
        if status_filter == "active" and today is not None:
            stmt = stmt.where(
                Budget.period_start <= today,
                Budget.period_end >= today,
            )
        elif status_filter == "upcoming" and today is not None:
            stmt = stmt.where(Budget.period_start > today)
        elif status_filter == "archived" and today is not None:
            stmt = stmt.where(Budget.period_end < today)

        if overlap_start is not None and overlap_end is not None:
            stmt = stmt.where(
                Budget.period_start <= overlap_end,
                Budget.period_end >= overlap_start,
            )
        if period_start_from is not None:
            stmt = stmt.where(Budget.period_start >= period_start_from)
        if period_end_to is not None:
            stmt = stmt.where(Budget.period_end <= period_end_to)

        stmt = stmt.order_by(
            Budget.period_start.asc(),
            Budget.name.asc(),
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def find_duplicate_budget(
        db: AsyncSession,
        user_id: UUID,
        *,
        scope: BudgetScope,
        category_id: UUID | None,
        category_group_id: UUID | None,
        period_start: date,
        period_end: date,
        exclude_budget_id: UUID | None = None,
    ) -> Budget | None:
        stmt = select(Budget).where(
            Budget.user_id == user_id,
            Budget.scope == scope,
            Budget.period_start == period_start,
            Budget.period_end == period_end,
        )
        if scope == BudgetScope.CATEGORY:
            stmt = stmt.where(Budget.category_id == category_id)
        else:
            stmt = stmt.where(Budget.category_group_id == category_group_id)
        if exclude_budget_id is not None:
            stmt = stmt.where(Budget.id != exclude_budget_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def create(db: AsyncSession, budget: Budget) -> Budget:
        db.add(budget)
        await db.flush()
        return budget

    @staticmethod
    async def delete(db: AsyncSession, budget: Budget) -> None:
        await db.delete(budget)
        await db.flush()

    @staticmethod
    async def calculate_spent_for_budget(
        db: AsyncSession,
        budget: Budget,
    ) -> Decimal:
        stmt = (
            select(func.coalesce(func.sum(Transaction.amount), 0))
            .select_from(Transaction)
            .join(Category, Transaction.category_id == Category.id)
            .where(
                Transaction.type == TransactionType.EXPENSE,
                Transaction.kind == TransactionKind.REGULAR,
                Transaction.deleted_at.is_(None),
                Transaction.transaction_date >= budget.period_start,
                Transaction.transaction_date <= budget.period_end,
            )
        )
        if budget.category_id is not None:
            stmt = stmt.where(Transaction.category_id == budget.category_id)
        if budget.category_group_id is not None:
            stmt = stmt.join(
                CategoryGroup,
                Category.group_id == CategoryGroup.id,
            )
            stmt = stmt.where(Category.group_id == budget.category_group_id)
        result = await db.execute(stmt)
        value = result.scalar_one()
        if isinstance(value, Decimal):
            return value
        return Decimal(str(value))
