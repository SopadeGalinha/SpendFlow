from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlmodel import (
    Column,
    DateTime,
    Field,
    Relationship,
    SQLModel,
    UniqueConstraint,
    func,
)

from src.models.category_group import CategoryGroup
from src.models.enums import CategoryType

if TYPE_CHECKING:
    from src.models.transaction import Transaction


class Category(SQLModel, table=True):
    """Category with system defaults and user custom entries."""

    __tablename__ = "categories"
    __table_args__ = (
        UniqueConstraint("group_id", "slug", name="uq_categories_group_slug"),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str = Field(nullable=False)
    slug: str = Field(index=True, nullable=False)
    type: CategoryType = Field(nullable=False, index=True)
    sort_order: int = Field(default=0, nullable=False)
    is_system: bool = Field(default=False, nullable=False)
    is_transfer: bool = Field(default=False, nullable=False)
    exclude_from_budget: bool = Field(default=False, nullable=False)
    group_id: UUID = Field(foreign_key="category_groups.id", index=True)
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

    group: CategoryGroup = Relationship(back_populates="categories")
    transactions: list["Transaction"] = Relationship(back_populates="category")


__all__ = ["Category"]
