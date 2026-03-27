from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field, field_serializer

from src.models import TransactionKind, TransactionType


class TransactionBase(BaseModel):
    description: str = Field(min_length=1, max_length=255)
    amount: Decimal = Field(gt=0)
    transaction_date: date
    account_id: UUID
    category_id: UUID | None = None


class TransactionCreate(TransactionBase):
    type: TransactionType


class TransactionUpdate(BaseModel):
    description: str | None = Field(default=None, min_length=1, max_length=255)
    amount: Decimal | None = Field(default=None, gt=0)
    transaction_date: date | None = None
    type: TransactionType | None = None
    category_id: UUID | None = None


class TransactionAdjustmentCreate(BaseModel):
    description: str = Field(min_length=1, max_length=255)
    amount: Decimal = Field(gt=0)
    type: TransactionType
    transaction_date: date
    account_id: UUID
    category_id: UUID | None = None


class TransferCreate(BaseModel):
    description: str = Field(min_length=1, max_length=255)
    amount: Decimal = Field(gt=0)
    transaction_date: date
    from_account_id: UUID
    to_account_id: UUID
    category_id: UUID | None = None


class TransactionResponse(BaseModel):
    id: UUID
    description: str
    amount: Decimal
    type: TransactionType
    kind: TransactionKind
    transaction_date: date
    account_id: UUID
    transfer_group_id: UUID | None
    category_id: UUID | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

    @field_serializer("amount")
    def serialize_amount(self, value: Decimal) -> str:
        return str(value)


class TransferResponse(BaseModel):
    transfer_group_id: UUID
    amount: Decimal
    transaction_date: date
    from_entry: TransactionResponse
    to_entry: TransactionResponse

    @field_serializer("amount")
    def serialize_amount(self, value: Decimal) -> str:
        return str(value)
