from decimal import Decimal

from pydantic import BaseModel  # type: ignore
from datetime import date
from uuid import UUID
# from typing import List
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

    class Config:
        from_attributes = True
        json_encoders = {
            Decimal: lambda v: str(v)
        }
