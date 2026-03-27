from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field, field_serializer, model_validator

from src.models import BudgetScope, BudgetStatus


class BudgetBase(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    amount: Decimal = Field(gt=0)
    period_start: date
    period_end: date
    scope: BudgetScope
    category_group_id: UUID | None = None
    category_id: UUID | None = None

    @model_validator(mode="after")
    def validate_scope_target(self):
        if self.period_end < self.period_start:
            raise ValueError("period_end must be on or after period_start")
        if self.scope == BudgetScope.GROUP:
            if self.category_group_id is None or self.category_id is not None:
                raise ValueError(
                    "Group budgets require category_group_id only."
                )
        if self.scope == BudgetScope.CATEGORY:
            if self.category_id is None or self.category_group_id is not None:
                raise ValueError("Category budgets require category_id only.")
        return self


class BudgetCreate(BudgetBase):
    pass


class BudgetCloneCreate(BaseModel):
    period_start: date
    period_end: date
    name: str | None = Field(default=None, min_length=1, max_length=255)
    amount: Decimal | None = Field(default=None, gt=0)

    @model_validator(mode="after")
    def validate_period(self):
        if self.period_end < self.period_start:
            raise ValueError("period_end must be on or after period_start")
        return self


class BudgetUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    amount: Decimal | None = Field(default=None, gt=0)
    period_start: date | None = None
    period_end: date | None = None

    @model_validator(mode="after")
    def validate_period(self):
        if (
            self.period_start is not None
            and self.period_end is not None
            and self.period_end < self.period_start
        ):
            raise ValueError("period_end must be on or after period_start")
        return self


class BudgetResponse(BaseModel):
    id: UUID
    name: str
    amount: Decimal
    period_start: date
    period_end: date
    scope: BudgetScope
    status: BudgetStatus
    category_group_id: UUID | None
    category_group_name: str | None = None
    category_group_slug: str | None = None
    category_id: UUID | None
    category_name: str | None = None
    category_slug: str | None = None
    spent: Decimal
    remaining: Decimal
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

    @field_serializer("amount", "spent", "remaining")
    def serialize_decimal(self, value: Decimal) -> str:
        return str(value)
