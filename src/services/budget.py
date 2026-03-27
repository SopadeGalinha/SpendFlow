from calendar import monthrange
from datetime import date
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import Budget, BudgetScope, BudgetStatus, CategoryType
from src.repositories import BudgetRepository, CategoryRepository
from src.schemas import (
    BudgetCloneCreate,
    BudgetCreate,
    BudgetResponse,
    BudgetUpdate,
)

DUPLICATE_BUDGET_DETAIL = (
    "A budget already exists for this target in the same period."
)


class BudgetService:
    @staticmethod
    def _metadata_for_budget(
        budget: Budget,
        categories_by_id,
        groups_by_id,
    ) -> dict:
        category_name = None
        category_slug = None
        category_group_id = budget.category_group_id
        category_group_name = None
        category_group_slug = None

        if budget.category_id is not None:
            category = categories_by_id.get(budget.category_id)
            if category is not None:
                category_name = category.name
                category_slug = category.slug
                category_group_id = category.group_id
                group = groups_by_id.get(category.group_id)
                if group is not None:
                    category_group_name = group.name
                    category_group_slug = group.slug
        elif budget.category_group_id is not None:
            group = groups_by_id.get(budget.category_group_id)
            if group is not None:
                category_group_name = group.name
                category_group_slug = group.slug

        return {
            "category_id": budget.category_id,
            "category_group_id": category_group_id,
            "category_group_name": category_group_name,
            "category_group_slug": category_group_slug,
            "category_name": category_name,
            "category_slug": category_slug,
        }

    @staticmethod
    def _budget_status(budget: Budget, today: date) -> BudgetStatus:
        if budget.period_end < today:
            return BudgetStatus.ARCHIVED
        if budget.period_start > today:
            return BudgetStatus.UPCOMING
        return BudgetStatus.ACTIVE

    @staticmethod
    def _resolve_month_window(
        year: int | None,
        month: int | None,
    ) -> tuple[date, date] | None:
        if month is not None and year is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="year is required when month is provided.",
            )
        if year is None:
            return None
        resolved_month = month or 1
        if month is None:
            return date(year, 1, 1), date(year, 12, 31)
        last_day = monthrange(year, resolved_month)[1]
        return (
            date(year, resolved_month, 1),
            date(year, resolved_month, last_day),
        )

    @classmethod
    async def _get_budget_or_404(
        cls,
        db: AsyncSession,
        user_id: UUID,
        budget_id: UUID,
    ) -> Budget:
        budget = await BudgetRepository.get_owned_budget(
            db,
            user_id,
            budget_id,
        )
        if budget is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Budget not found.",
            )
        return budget

    @classmethod
    async def _ensure_unique_budget_period(
        cls,
        db: AsyncSession,
        user_id: UUID,
        *,
        scope: BudgetScope,
        category_id: UUID | None,
        category_group_id: UUID | None,
        period_start: date,
        period_end: date,
        exclude_budget_id: UUID | None = None,
    ) -> None:
        duplicate = await BudgetRepository.find_duplicate_budget(
            db,
            user_id,
            scope=scope,
            category_id=category_id,
            category_group_id=category_group_id,
            period_start=period_start,
            period_end=period_end,
            exclude_budget_id=exclude_budget_id,
        )
        if duplicate is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=DUPLICATE_BUDGET_DETAIL,
            )

    @staticmethod
    async def _validate_scope_target(
        db: AsyncSession,
        user_id: UUID,
        budget_in: BudgetCreate,
    ) -> None:
        if budget_in.scope == BudgetScope.GROUP:
            group = await CategoryRepository.get_accessible_group(
                db,
                user_id,
                budget_in.category_group_id,
            )
            if group is None or group.type != CategoryType.EXPENSE:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Expense category group not found.",
                )
            return

        category = await CategoryRepository.get_accessible_category(
            db,
            user_id,
            budget_in.category_id,
        )
        if category is None or category.type != CategoryType.EXPENSE:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Expense category not found.",
            )

    @staticmethod
    async def _to_response(
        db: AsyncSession,
        budget: Budget,
        today: date | None = None,
        categories_by_id: dict | None = None,
        groups_by_id: dict | None = None,
    ) -> BudgetResponse:
        today = today or date.today()
        categories_by_id = categories_by_id or {}
        groups_by_id = groups_by_id or {}
        spent = await BudgetRepository.calculate_spent_for_budget(db, budget)
        return BudgetResponse(
            **budget.model_dump(
                exclude={
                    "category_group_id",
                    "category_id",
                }
            ),
            status=BudgetService._budget_status(budget, today),
            **BudgetService._metadata_for_budget(
                budget,
                categories_by_id,
                groups_by_id,
            ),
            spent=spent,
            remaining=budget.amount - spent,
        )

    @classmethod
    async def create_budget(
        cls,
        db: AsyncSession,
        user_id: UUID,
        budget_in: BudgetCreate,
    ) -> BudgetResponse:
        await cls._validate_scope_target(db, user_id, budget_in)
        await cls._ensure_unique_budget_period(
            db,
            user_id,
            scope=budget_in.scope,
            category_id=budget_in.category_id,
            category_group_id=budget_in.category_group_id,
            period_start=budget_in.period_start,
            period_end=budget_in.period_end,
        )
        budget = Budget(user_id=user_id, **budget_in.model_dump())
        try:
            await BudgetRepository.create(db, budget)
            await db.commit()
        except IntegrityError:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=DUPLICATE_BUDGET_DETAIL,
            )
        await db.refresh(budget)
        categories_by_id, groups_by_id = (
            await BudgetRepository.load_target_metadata(db, [budget])
        )
        return await cls._to_response(
            db,
            budget,
            categories_by_id=categories_by_id,
            groups_by_id=groups_by_id,
        )

    @classmethod
    async def list_budgets(
        cls,
        db: AsyncSession,
        user_id: UUID,
        *,
        status_filter: BudgetStatus | None = None,
        year: int | None = None,
        month: int | None = None,
        period_start_from: date | None = None,
        period_end_to: date | None = None,
    ) -> list[BudgetResponse]:
        today = date.today()
        month_window = cls._resolve_month_window(year, month)
        overlap_start = None
        overlap_end = None
        if month_window is not None:
            overlap_start, overlap_end = month_window
        budgets = await BudgetRepository.list_owned_budgets(
            db,
            user_id,
            today=today,
            status_filter=status_filter.value if status_filter else None,
            overlap_start=overlap_start,
            overlap_end=overlap_end,
            period_start_from=period_start_from,
            period_end_to=period_end_to,
        )
        categories_by_id, groups_by_id = (
            await BudgetRepository.load_target_metadata(db, budgets)
        )
        return [
            await cls._to_response(
                db,
                budget,
                today=today,
                categories_by_id=categories_by_id,
                groups_by_id=groups_by_id,
            )
            for budget in budgets
        ]

    @classmethod
    async def get_budget(
        cls,
        db: AsyncSession,
        user_id: UUID,
        budget_id: UUID,
    ) -> BudgetResponse:
        budget = await cls._get_budget_or_404(db, user_id, budget_id)
        categories_by_id, groups_by_id = (
            await BudgetRepository.load_target_metadata(db, [budget])
        )
        return await cls._to_response(
            db,
            budget,
            categories_by_id=categories_by_id,
            groups_by_id=groups_by_id,
        )

    @classmethod
    async def update_budget(
        cls,
        db: AsyncSession,
        user_id: UUID,
        budget_id: UUID,
        budget_in: BudgetUpdate,
    ) -> BudgetResponse:
        budget = await cls._get_budget_or_404(db, user_id, budget_id)

        if budget_in.name is not None:
            budget.name = budget_in.name
        if budget_in.amount is not None:
            budget.amount = budget_in.amount
        if budget_in.period_start is not None:
            budget.period_start = budget_in.period_start
        if budget_in.period_end is not None:
            budget.period_end = budget_in.period_end
        if budget.period_end < budget.period_start:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="period_end must be on or after period_start.",
            )

        await cls._ensure_unique_budget_period(
            db,
            user_id,
            scope=budget.scope,
            category_id=budget.category_id,
            category_group_id=budget.category_group_id,
            period_start=budget.period_start,
            period_end=budget.period_end,
            exclude_budget_id=budget.id,
        )

        db.add(budget)
        try:
            await db.commit()
        except IntegrityError:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=DUPLICATE_BUDGET_DETAIL,
            )
        await db.refresh(budget)
        categories_by_id, groups_by_id = (
            await BudgetRepository.load_target_metadata(db, [budget])
        )
        return await cls._to_response(
            db,
            budget,
            categories_by_id=categories_by_id,
            groups_by_id=groups_by_id,
        )

    @classmethod
    async def clone_budget(
        cls,
        db: AsyncSession,
        user_id: UUID,
        source_budget_id: UUID,
        clone_in: BudgetCloneCreate,
    ) -> BudgetResponse:
        source_budget = await cls._get_budget_or_404(
            db,
            user_id,
            source_budget_id,
        )
        await cls._ensure_unique_budget_period(
            db,
            user_id,
            scope=source_budget.scope,
            category_id=source_budget.category_id,
            category_group_id=source_budget.category_group_id,
            period_start=clone_in.period_start,
            period_end=clone_in.period_end,
        )

        cloned_budget = Budget(
            user_id=user_id,
            name=clone_in.name or source_budget.name,
            amount=clone_in.amount or source_budget.amount,
            period_start=clone_in.period_start,
            period_end=clone_in.period_end,
            scope=source_budget.scope,
            category_id=source_budget.category_id,
            category_group_id=source_budget.category_group_id,
        )
        try:
            await BudgetRepository.create(db, cloned_budget)
            await db.commit()
        except IntegrityError:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=DUPLICATE_BUDGET_DETAIL,
            )
        await db.refresh(cloned_budget)
        categories_by_id, groups_by_id = (
            await BudgetRepository.load_target_metadata(db, [cloned_budget])
        )
        return await cls._to_response(
            db,
            cloned_budget,
            categories_by_id=categories_by_id,
            groups_by_id=groups_by_id,
        )

    @staticmethod
    async def delete_budget(
        db: AsyncSession,
        user_id: UUID,
        budget_id: UUID,
    ) -> None:
        budget = await BudgetService._get_budget_or_404(
            db,
            user_id,
            budget_id,
        )
        await BudgetRepository.delete(db, budget)
        await db.commit()
