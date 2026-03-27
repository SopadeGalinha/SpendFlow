from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_serializer

from src.models import AccountType


class AccountBase(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    account_type: AccountType = AccountType.CHECKING


class AccountCreate(AccountBase):
    model_config = {"extra": "forbid"}
    opening_balance: Optional[Decimal] = Field(None, ge=0)


class AccountUpdate(BaseModel):
    model_config = {"extra": "forbid"}
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    account_type: Optional[AccountType] = None


class AccountResponse(AccountBase):
    id: UUID
    balance: Decimal

    model_config = {"from_attributes": True}

    @field_serializer("balance")
    def serialize_balance(self, value: Decimal) -> str:
        return str(value)
