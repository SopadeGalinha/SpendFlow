from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlmodel import Column, DateTime, Field, Relationship, SQLModel, func

from src.models.enums import CategoryType

if TYPE_CHECKING:
    from src.models.category import Category


class CategoryGroup(SQLModel, table=True):
    """Grouping layer for categories used by budgets and dashboards."""

    __tablename__ = "category_groups"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str = Field(nullable=False)
    slug: str = Field(index=True, nullable=False)
    type: CategoryType = Field(nullable=False, index=True)
    sort_order: int = Field(default=0, nullable=False)
    is_system: bool = Field(default=False, nullable=False)
    user_id: UUID | None = Field(
        default=None,
        foreign_key="user.id",
        index=True,
    )
    created_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True),
            nullable=False,
            server_default=func.now(),
        )
    )
    updated_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True),
            nullable=False,
            server_default=func.now(),
            onupdate=func.now(),
        )
    )

    categories: list["Category"] = Relationship(back_populates="group")


__all__ = ["CategoryGroup"]
