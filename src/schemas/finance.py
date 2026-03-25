from datetime import date
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, field_serializer

from src.models import TransactionType


class ProjectionResponse(BaseModel):
    id: str
    description: str
    amount: Decimal
    type: TransactionType
    original_date: date
    date: date
    is_virtual: bool
    rule_id: UUID

    model_config = {"from_attributes": True}

    @field_serializer("amount")
    def serialize_amount(self, value: Decimal) -> str:
        return str(value)
