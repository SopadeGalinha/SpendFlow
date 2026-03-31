from datetime import datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID, uuid4

from sqlalchemy import JSON
from sqlmodel import (
    Column,
    DateTime,
    Field,
    Relationship,
    SQLModel,
    func,
)

from src.models.enums import WeekendAdjustment

if TYPE_CHECKING:
    from src.models.account import Account


class User(SQLModel, table=True):
    """Core User model for SpendFlow.
    Includes SaaS-ready fields for regional settings.
    """

    id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
        index=True,
        description="Unique identifier for the user",
    )
    username: str = Field(index=True, unique=True, nullable=False)
    email: str = Field(index=True, unique=True, nullable=False)
    hashed_password: str = Field(nullable=False)

    city: str | None = Field(default=None)
    timezone: str = Field(
        default="UTC",
        description="User's local timezone (e.g., Europe/Lisbon)",
    )
    currency: str = Field(
        default="EUR",
        description="Primary currency for display",
    )
    ui_preferences: dict[str, Any] | None = Field(
        default=None,
        sa_column=Column(JSON, nullable=True),
        description="Optional per-user UI preferences for web experience",
    )

    default_weekend_adjustment: WeekendAdjustment = Field(
        default=WeekendAdjustment.KEEP,
        description="Default rule for weekend date shifting",
    )
    created_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True), nullable=False, server_default=func.now()
        ),
        description="Timestamp when the user was created",
    )
    updated_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True),
            nullable=False,
            server_default=func.now(),
            onupdate=func.now(),
        ),
        description="Timestamp when the user was last updated",
    )

    accounts: list["Account"] = Relationship(back_populates="user")
