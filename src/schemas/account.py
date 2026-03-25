from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_serializer


class AccountBase(BaseModel):
    name: str = Field(min_length=1, max_length=255)


class AccountCreate(AccountBase):
    balance: Optional[Decimal] = Field(None, ge=0)


class AccountUpdate(AccountBase):
    balance: Optional[Decimal] = Field(None, ge=0)


class AccountResponse(AccountBase):
    id: UUID
    balance: Decimal

    model_config = {"from_attributes": True}

    @field_serializer("balance")
    def serialize_balance(self, value: Decimal) -> str:
        return str(value)
