import logging
import re
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import Category, CategoryGroup, CategoryType
from src.repositories import CategoryRepository
from src.schemas import CategoryCreate, CategoryGroupCreate

logger = logging.getLogger(__name__)

DEFAULT_CATEGORY_CATALOG: list[dict] = [
    {
        "name": "Income",
        "slug": "income",
        "type": CategoryType.INCOME,
        "sort_order": 10,
        "categories": [
            "Salary",
            "Freelance",
            "Business",
            "Investment",
            "Bonus",
            "Gift",
            "Refund",
            "Other Income",
        ],
    },
    {
        "name": "Home",
        "slug": "home",
        "type": CategoryType.EXPENSE,
        "sort_order": 20,
        "categories": ["Housing", "Utilities", "Insurance"],
    },
    {
        "name": "Living",
        "slug": "living",
        "type": CategoryType.EXPENSE,
        "sort_order": 30,
        "categories": [
            "Groceries",
            "Transport",
            "Health",
            "Education",
            "Eating Out",
        ],
    },
    {
        "name": "Lifestyle",
        "slug": "lifestyle",
        "type": CategoryType.EXPENSE,
        "sort_order": 40,
        "categories": [
            "Entertainment",
            "Shopping",
            "Subscriptions",
            "Travel",
        ],
    },
    {
        "name": "Financial",
        "slug": "financial",
        "type": CategoryType.EXPENSE,
        "sort_order": 50,
        "categories": [
            "Taxes",
            "Savings",
            "Debt Payment",
            "Investment",
        ],
    },
    {
        "name": "Pets",
        "slug": "pets",
        "type": CategoryType.EXPENSE,
        "sort_order": 60,
        "categories": ["Pets"],
    },
    {
        "name": "Transfers",
        "slug": "transfers",
        "type": CategoryType.TRANSFER,
        "sort_order": 70,
        "categories": [
            "Transfer",
            "Credit Card Payment",
            "Loan Payment",
        ],
    },
]


class CategoryService:
    @staticmethod
    def _slugify(value: str) -> str:
        slug = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
        return slug or "category"

    @classmethod
    async def ensure_default_catalog(
        cls,
        db: AsyncSession,
    ) -> None:
        existing_groups = await CategoryRepository.list_system_groups(db)
        existing_group_slugs = {
            (group.slug, group.type): group
            for group in existing_groups
        }
        created_any = False

        for group_index, group_data in enumerate(
            DEFAULT_CATEGORY_CATALOG,
            start=1,
        ):
            key = (group_data["slug"], group_data["type"])
            group = existing_group_slugs.get(key)
            if group is None:
                group = await CategoryRepository.create_group(
                    db,
                    CategoryGroup(
                        name=group_data["name"],
                        slug=group_data["slug"],
                        type=group_data["type"],
                        sort_order=group_data["sort_order"],
                        is_system=True,
                    ),
                )
                created_any = True

            for category_index, category_name in enumerate(
                group_data["categories"],
                start=1,
            ):
                category_slug = cls._slugify(category_name)
                existing_category = (
                    await CategoryRepository.find_system_category_by_slug(
                        db,
                        group.id,
                        category_slug,
                    )
                )
                if existing_category is not None:
                    continue

                is_transfer = group_data["type"] == CategoryType.TRANSFER
                await CategoryRepository.create_category(
                    db,
                    Category(
                        name=category_name,
                        slug=category_slug,
                        type=group_data["type"],
                        sort_order=(group_index * 100) + category_index,
                        is_system=True,
                        is_transfer=is_transfer,
                        exclude_from_budget=is_transfer,
                        group_id=group.id,
                    ),
                )
                created_any = True

        if created_any:
            try:
                await db.commit()
            except IntegrityError:
                await db.rollback()
        else:
            await db.rollback()

    @classmethod
    async def bootstrap_system_catalog(cls, db: AsyncSession) -> None:
        await cls.ensure_default_catalog(db)

    @classmethod
    async def list_groups(
        cls,
        db: AsyncSession,
        user_id: UUID,
        category_type: CategoryType | None = None,
    ) -> list[CategoryGroup]:
        return await CategoryRepository.list_groups(db, user_id, category_type)

    @classmethod
    async def list_categories(
        cls,
        db: AsyncSession,
        user_id: UUID,
        category_type: CategoryType | None = None,
        group_id: UUID | None = None,
    ) -> list[Category]:
        if group_id is not None:
            group = await CategoryRepository.get_accessible_group(
                db,
                user_id,
                group_id,
            )
            if group is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Category group not found.",
                )
        return await CategoryRepository.list_categories(
            db,
            user_id,
            category_type,
            group_id,
        )

    @classmethod
    async def get_catalog(
        cls,
        db: AsyncSession,
        user_id: UUID,
        category_type: CategoryType | None = None,
    ) -> list[dict]:
        groups = await cls.list_groups(db, user_id, category_type)
        categories = await cls.list_categories(db, user_id, category_type)
        categories_by_group: dict[UUID, list[Category]] = {}
        for category in categories:
            categories_by_group.setdefault(
                category.group_id,
                [],
            ).append(category)

        catalog = []
        for group in groups:
            catalog.append(
                {
                    **group.model_dump(),
                    "categories": categories_by_group.get(group.id, []),
                }
            )
        return catalog

    @classmethod
    async def create_group(
        cls,
        db: AsyncSession,
        user_id: UUID,
        group_data: CategoryGroupCreate,
    ) -> CategoryGroup:
        slug = cls._slugify(group_data.name)
        existing_group = await CategoryRepository.find_group_by_slug(
            db,
            user_id,
            slug,
            group_data.type,
        )
        if existing_group is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Category group already exists.",
            )

        groups = await CategoryRepository.list_groups(
            db,
            user_id,
            group_data.type,
        )
        group = CategoryGroup(
            name=group_data.name,
            slug=slug,
            type=group_data.type,
            sort_order=(len(groups) + 1) * 100,
            user_id=user_id,
            is_system=False,
        )
        try:
            created_group = await CategoryRepository.create_group(db, group)
            await db.commit()
        except IntegrityError:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Category group already exists.",
            )
        await db.refresh(created_group)
        logger.info(
            "Category group created",
            extra={"group_id": str(created_group.id), "user_id": str(user_id)},
        )
        return created_group

    @classmethod
    async def create_category(
        cls,
        db: AsyncSession,
        user_id: UUID,
        category_data: CategoryCreate,
    ) -> Category:
        group = await CategoryRepository.get_accessible_group(
            db,
            user_id,
            category_data.group_id,
        )
        if group is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category group not found.",
            )
        if group.type != category_data.type:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Category type must match the group type.",
            )

        slug = cls._slugify(category_data.name)
        existing_category = await CategoryRepository.find_category_by_slug(
            db,
            user_id,
            group.id,
            slug,
        )
        if existing_category is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Category already exists in this group.",
            )

        categories = await CategoryRepository.list_categories(
            db,
            user_id,
            group_id=group.id,
        )
        category = Category(
            name=category_data.name,
            slug=slug,
            type=category_data.type,
            sort_order=(len(categories) + 1) * 10,
            user_id=user_id,
            is_system=False,
            is_transfer=category_data.type == CategoryType.TRANSFER,
            exclude_from_budget=category_data.type == CategoryType.TRANSFER,
            group_id=group.id,
        )
        try:
            created_category = await CategoryRepository.create_category(
                db,
                category,
            )
            await db.commit()
        except IntegrityError:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Category already exists in this group.",
            )
        await db.refresh(created_category)
        logger.info(
            "Category created",
            extra={
                "category_id": str(created_category.id),
                "group_id": str(group.id),
                "user_id": str(user_id),
            },
        )
        return created_category
