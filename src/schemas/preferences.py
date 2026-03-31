from typing import Literal

from pydantic import BaseModel, Field, field_validator

DASHBOARD_WIDGET_IDS = (
    "metrics",
    "evolution",
    "accounts_savings",
    "budgets_recurring",
    "calendar",
    "transactions",
)


def normalize_widget_order(value: object) -> list[str]:
    if not isinstance(value, list):
        return list(DASHBOARD_WIDGET_IDS)

    normalized: list[str] = []
    for candidate in value:
        if isinstance(candidate, str) and candidate in DASHBOARD_WIDGET_IDS:
            if candidate not in normalized:
                normalized.append(candidate)

    for widget_id in DASHBOARD_WIDGET_IDS:
        if widget_id not in normalized:
            normalized.append(widget_id)

    return normalized


def normalize_hidden_widgets(value: object) -> list[str]:
    if not isinstance(value, list):
        return []

    normalized: list[str] = []
    for candidate in value:
        if isinstance(candidate, str) and candidate in DASHBOARD_WIDGET_IDS:
            if candidate not in normalized:
                normalized.append(candidate)

    return normalized


class DashboardPreferences(BaseModel):
    order: list[str] = Field(default_factory=lambda: list(DASHBOARD_WIDGET_IDS))
    hidden: list[str] = Field(default_factory=list)

    @field_validator("order", mode="before")
    @classmethod
    def validate_order(cls, value: object) -> list[str]:
        return normalize_widget_order(value)

    @field_validator("hidden", mode="before")
    @classmethod
    def validate_hidden(cls, value: object) -> list[str]:
        return normalize_hidden_widgets(value)


class BudgetPreferences(BaseModel):
    view_mode: Literal["category", "flex"] = "category"


class UserPreferencesResponse(BaseModel):
    dashboard: DashboardPreferences = Field(default_factory=DashboardPreferences)
    budget: BudgetPreferences = Field(default_factory=BudgetPreferences)


class DashboardPreferencesUpdate(BaseModel):
    order: list[str] | None = None
    hidden: list[str] | None = None

    @field_validator("order", mode="before")
    @classmethod
    def validate_order(cls, value: object) -> list[str] | None:
        if value is None:
            return None
        return normalize_widget_order(value)

    @field_validator("hidden", mode="before")
    @classmethod
    def validate_hidden(cls, value: object) -> list[str] | None:
        if value is None:
            return None
        return normalize_hidden_widgets(value)


class BudgetPreferencesUpdate(BaseModel):
    view_mode: Literal["category", "flex"] | None = None


class UserPreferencesUpdate(BaseModel):
    dashboard: DashboardPreferencesUpdate | None = None
    budget: BudgetPreferencesUpdate | None = None
