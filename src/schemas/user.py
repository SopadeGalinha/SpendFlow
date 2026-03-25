from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, field_validator


class UserBase(BaseModel):
    username: str
    email: EmailStr
    city: str | None = None
    timezone: str = "UTC"
    currency: str = "EUR"
    default_weekend_adjustment: str = "keep"


class UserCreate(UserBase):
    password: str

    @field_validator("password")
    @classmethod
    def validate_password_length(cls, value: str) -> str:
        if len(value) > 72:
            raise ValueError("Password cannot be longer than 72 characters.")
        if len(value) < 8:
            raise ValueError("Password must be at least 8 characters long.")
        return value


class UserResponse(UserBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class Token(BaseModel):
    access_token: str
    token_type: str
