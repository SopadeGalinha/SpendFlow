from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import Category, CategoryGroup, CategoryType


class CategoryRepository:
    @staticmethod
    async def list_system_groups(db: AsyncSession) -> list[CategoryGroup]:
        stmt = select(CategoryGroup).where(CategoryGroup.is_system.is_(True))
        stmt = stmt.order_by(
            CategoryGroup.sort_order.asc(),
            CategoryGroup.name.asc(),
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def list_groups(
        db: AsyncSession,
        user_id: UUID,
        category_type: CategoryType | None = None,
    ) -> list[CategoryGroup]:
        stmt = select(CategoryGroup).where(
            or_(
                CategoryGroup.is_system.is_(True),
                CategoryGroup.user_id == user_id,
            )
        )
        if category_type is not None:
            stmt = stmt.where(CategoryGroup.type == category_type)
        stmt = stmt.order_by(
            CategoryGroup.sort_order.asc(),
            CategoryGroup.name.asc(),
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def list_categories(
        db: AsyncSession,
        user_id: UUID,
        category_type: CategoryType | None = None,
        group_id: UUID | None = None,
    ) -> list[Category]:
        stmt = select(Category).where(
            or_(
                Category.is_system.is_(True),
                Category.user_id == user_id,
            )
        )
        if category_type is not None:
            stmt = stmt.where(Category.type == category_type)
        if group_id is not None:
            stmt = stmt.where(Category.group_id == group_id)
        stmt = stmt.order_by(Category.sort_order.asc(), Category.name.asc())
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def get_accessible_group(
        db: AsyncSession,
        user_id: UUID,
        group_id: UUID,
    ) -> CategoryGroup | None:
        stmt = select(CategoryGroup).where(
            CategoryGroup.id == group_id,
            or_(
                CategoryGroup.is_system.is_(True),
                CategoryGroup.user_id == user_id,
            ),
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_accessible_category(
        db: AsyncSession,
        user_id: UUID,
        category_id: UUID,
    ) -> Category | None:
        stmt = select(Category).where(
            Category.id == category_id,
            or_(
                Category.is_system.is_(True),
                Category.user_id == user_id,
            ),
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def find_system_group_by_slug(
        db: AsyncSession,
        slug: str,
        category_type: CategoryType,
    ) -> CategoryGroup | None:
        stmt = select(CategoryGroup).where(
            CategoryGroup.slug == slug,
            CategoryGroup.type == category_type,
            CategoryGroup.is_system.is_(True),
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def find_group_by_slug(
        db: AsyncSession,
        user_id: UUID,
        slug: str,
        category_type: CategoryType,
    ) -> CategoryGroup | None:
        stmt = select(CategoryGroup).where(
            CategoryGroup.slug == slug,
            CategoryGroup.type == category_type,
            or_(
                CategoryGroup.is_system.is_(True),
                CategoryGroup.user_id == user_id,
            ),
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def find_system_category_by_slug(
        db: AsyncSession,
        group_id: UUID,
        slug: str,
    ) -> Category | None:
        stmt = select(Category).where(
            Category.group_id == group_id,
            Category.slug == slug,
            Category.is_system.is_(True),
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def find_system_category_by_type_and_slug(
        db: AsyncSession,
        category_type: CategoryType,
        slug: str,
    ) -> Category | None:
        stmt = select(Category).where(
            Category.type == category_type,
            Category.slug == slug,
            Category.is_system.is_(True),
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def find_category_by_slug(
        db: AsyncSession,
        user_id: UUID,
        group_id: UUID,
        slug: str,
    ) -> Category | None:
        stmt = select(Category).where(
            Category.group_id == group_id,
            Category.slug == slug,
            or_(
                Category.is_system.is_(True),
                Category.user_id == user_id,
            ),
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def create_group(
        db: AsyncSession,
        group: CategoryGroup,
    ) -> CategoryGroup:
        db.add(group)
        await db.flush()
        return group

    @staticmethod
    async def create_category(
        db: AsyncSession,
        category: Category,
    ) -> Category:
        db.add(category)
        await db.flush()
        return category
