from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.v1.deps import get_current_user
from src.database import get_session
from src.models import CategoryType, User
from src.schemas import (
    CategoryCatalogGroupResponse,
    CategoryCreate,
    CategoryGroupCreate,
    CategoryGroupResponse,
    CategoryResponse,
)
from src.services import CategoryService

router = APIRouter()


@router.get("/groups", response_model=list[CategoryGroupResponse])
async def list_category_groups(
    category_type: CategoryType | None = Query(None, alias="type"),
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return await CategoryService.list_groups(
        db,
        current_user.id,
        category_type,
    )


@router.post(
    "/groups",
    response_model=CategoryGroupResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_category_group(
    group_in: CategoryGroupCreate,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return await CategoryService.create_group(db, current_user.id, group_in)


@router.get("", response_model=list[CategoryResponse])
async def list_categories(
    category_type: CategoryType | None = Query(None, alias="type"),
    group_id: UUID | None = Query(None),
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return await CategoryService.list_categories(
        db,
        current_user.id,
        category_type,
        group_id,
    )


@router.get("/catalog", response_model=list[CategoryCatalogGroupResponse])
async def get_category_catalog(
    category_type: CategoryType | None = Query(None, alias="type"),
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return await CategoryService.get_catalog(
        db,
        current_user.id,
        category_type,
    )


@router.post(
    "",
    response_model=CategoryResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_category(
    category_in: CategoryCreate,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return await CategoryService.create_category(
        db,
        current_user.id,
        category_in,
    )
