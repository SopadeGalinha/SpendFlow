from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from src.models import CategoryType


class CategoryGroupBase(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    type: CategoryType


class CategoryGroupCreate(CategoryGroupBase):
    pass


class CategoryGroupResponse(CategoryGroupBase):
    id: UUID
    slug: str
    sort_order: int
    is_system: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CategoryBase(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    type: CategoryType


class CategoryCreate(CategoryBase):
    group_id: UUID


class CategoryResponse(CategoryBase):
    id: UUID
    slug: str
    sort_order: int
    is_system: bool
    is_transfer: bool
    exclude_from_budget: bool
    group_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CategoryCatalogGroupResponse(CategoryGroupResponse):
    categories: list[CategoryResponse]
