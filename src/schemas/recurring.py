from datetime import date
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field, field_serializer, model_validator

from src.models import Frequency, TransactionType, WeekendAdjustment


class RecurringRuleBase(BaseModel):
    description: str = Field(min_length=1, max_length=255)
    amount: Decimal = Field(gt=0)
    type: TransactionType
    frequency: Frequency
    interval: int = Field(default=1, ge=1)
    start_date: date
    end_date: date | None = None
    weekend_adjustment: WeekendAdjustment = WeekendAdjustment.KEEP

    @model_validator(mode="after")
    def validate_date_range(self):
        if self.end_date is not None and self.end_date < self.start_date:
            raise ValueError("end_date must be on or after start_date")
        return self


class RecurringRuleCreate(RecurringRuleBase):
    account_id: UUID


class RecurringRuleUpdate(BaseModel):
    description: str | None = Field(default=None, min_length=1, max_length=255)
    amount: Decimal | None = Field(default=None, gt=0)
    type: TransactionType | None = None
    frequency: Frequency | None = None
    interval: int | None = Field(default=None, ge=1)
    start_date: date | None = None
    end_date: date | None = None
    weekend_adjustment: WeekendAdjustment | None = None


class RecurringRuleResponse(BaseModel):
    id: UUID
    description: str
    amount: Decimal
    type: TransactionType
    frequency: Frequency
    interval: int
    start_date: date
    end_date: date | None
    weekend_adjustment: WeekendAdjustment
    account_id: UUID

    model_config = {"from_attributes": True}

    @field_serializer("amount")
    def serialize_amount(self, value: Decimal) -> str:
        return str(value)
