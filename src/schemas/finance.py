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
    balance_delta: Decimal = Decimal("0.00")
    projected_balance: Decimal | None = None

    model_config = {"from_attributes": True}

    @field_serializer("amount", "balance_delta", "projected_balance")
    def serialize_decimal(self, value: Decimal | None) -> str | None:
        if value is None:
            return None
        return str(value)
