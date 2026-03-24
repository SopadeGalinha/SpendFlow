from pydantic import BaseModel, EmailStr
from uuid import UUID
from datetime import datetime


class UserBase(BaseModel):
    username: str
    email: EmailStr
    city: str | None = None
    timezone: str = "UTC"
    currency: str = "EUR"
    default_weekend_adjustment: str = "keep"


class UserCreate(UserBase):
    password: str


class UserResponse(UserBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str
