from pydantic import BaseModel
from uuid import UUID
from decimal import Decimal
from typing import Optional


class AccountBase(BaseModel):
    name: str


class AccountCreate(AccountBase):
    balance: Optional[Decimal] = None


class AccountUpdate(AccountBase):
    balance: Optional[Decimal] = None


class AccountResponse(AccountBase):
    id: UUID
    balance: Decimal

    class Config:
        from_attributes = True
        json_encoders = {Decimal: str}
