"""Tests for models and data schemas validation."""

from datetime import datetime
from decimal import Decimal
from uuid import uuid4

import pytest
from pydantic import ValidationError

from src.models.enums import AccountType, BudgetScope, TransactionType
from src.schemas.account import AccountCreate, AccountUpdate
from src.schemas.budget import BudgetCloneCreate, BudgetCreate
from src.schemas.finance import ProjectionResponse
from src.schemas.recurring import RecurringRuleCreate, RecurringRuleUpdate
from src.schemas.user import UserCreate


class TestUserCreateSchema:
    """Test UserCreate schema validation."""

    def test_valid_user_creation(self):
        """Test creating user with valid data."""
        user_data = UserCreate(
            username="testuser",
            email="test@example.com",
            password="SecurePassword123",
            timezone="Europe/Lisbon",
            currency="EUR",
        )
        assert user_data.username == "testuser"
        assert user_data.email == "test@example.com"
        assert user_data.timezone == "Europe/Lisbon"

    def test_user_password_too_short(self):
        """Test that password shorter than 8 characters fails."""
        with pytest.raises(ValidationError):
            UserCreate(
                username="testuser",
                email="test@example.com",
                password="Short1",
            )

    def test_user_password_too_long(self):
        """Test that password longer than 72 characters fails."""
        with pytest.raises(ValidationError):
            UserCreate(
                username="testuser",
                email="test@example.com",
                password="a" * 73,
            )

    def test_user_invalid_email(self):
        """Test that invalid email fails."""
        with pytest.raises(ValidationError):
            UserCreate(
                username="testuser",
                email="not-an-email",
                password="ValidPassword123",
            )

    def test_user_missing_required_field(self):
        """Test that missing required field fails."""
        with pytest.raises(ValidationError):
            UserCreate(
                username="testuser",
                email="test@example.com",
            )

    def test_user_default_values(self):
        """Test that default values are applied."""
        user_data = UserCreate(
            username="testuser",
            email="test@example.com",
            password="ValidPassword123",
        )
        assert user_data.timezone == "UTC"
        assert user_data.currency == "EUR"
        assert user_data.default_weekend_adjustment == "keep"


class TestAccountCreateSchema:
    """Test AccountCreate schema validation."""

    def test_valid_account_creation(self):
        """Test creating account with valid data."""
        account_data = AccountCreate(
            name="Checking Account",
            account_type=AccountType.CHECKING,
            opening_balance=Decimal("1000.00"),
        )
        assert account_data.name == "Checking Account"
        assert account_data.opening_balance == Decimal("1000.00")

    def test_account_empty_name(self):
        """Test that empty account name fails."""
        with pytest.raises(ValidationError):
            AccountCreate(
                name="",
                opening_balance=Decimal("100.00"),
            )

    def test_account_name_too_long(self):
        """Test that account name longer than 255 chars fails."""
        with pytest.raises(ValidationError):
            AccountCreate(
                name="a" * 256,
                opening_balance=Decimal("100.00"),
            )

    def test_account_negative_balance(self):
        """Test that negative balance fails."""
        with pytest.raises(ValidationError):
            AccountCreate(
                name="Test",
                opening_balance=Decimal("-100.00"),
            )

    def test_account_default_balance(self):
        """Test that opening balance defaults to None."""
        account_data = AccountCreate(
            name="Test Account",
        )
        assert account_data.opening_balance is None

    def test_account_zero_balance(self):
        """Test that zero balance is valid."""
        account_data = AccountCreate(
            name="Test",
            opening_balance=Decimal("0.00"),
        )
        assert account_data.opening_balance == Decimal("0.00")

    def test_account_rejects_deprecated_balance_field(self):
        with pytest.raises(ValidationError):
            AccountCreate(name="Test", balance=Decimal("100.00"))


class TestAccountUpdateSchema:
    """Test AccountUpdate schema validation."""

    def test_valid_account_update(self):
        """Test updating account with valid data."""
        update_data = AccountUpdate(
            name="New Name",
            account_type=AccountType.SAVINGS,
        )
        assert update_data.name == "New Name"
        assert update_data.account_type == AccountType.SAVINGS

    def test_account_update_partial(self):
        """Test partial account update."""
        update_data = AccountUpdate(
            name="New Name",
        )
        assert update_data.name == "New Name"
        assert update_data.account_type is None

    def test_account_update_rejects_deprecated_balance_field(self):
        with pytest.raises(ValidationError):
            AccountUpdate(name="Test", balance=Decimal("-50.00"))


class TestProjectionResponseSchema:
    """Test ProjectionResponse schema validation."""

    def test_valid_projection(self):
        """Test creating valid projection response."""
        projection = ProjectionResponse(
            id="virtual_proj_123",
            description="Monthly salary",
            amount=Decimal("2000.00"),
            type=TransactionType.INCOME,
            original_date=datetime.now().date(),
            date=datetime.now().date(),
            is_virtual=True,
            rule_id=uuid4(),
        )
        assert projection.description == "Monthly salary"
        assert projection.amount == Decimal("2000.00")
        assert projection.is_virtual is True

    def test_projection_response_serialization(self):
        """Test that projection can be serialized to JSON."""
        from datetime import date

        projection = ProjectionResponse(
            id="virtual_proj_456",
            description="Monthly expense",
            amount=Decimal("800.00"),
            type=TransactionType.EXPENSE,
            original_date=date(2026, 3, 1),
            date=date(2026, 3, 1),
            is_virtual=True,
            rule_id=uuid4(),
        )
        json_data = projection.model_dump_json()
        assert "virtual_proj_456" in json_data
        assert "800.00" in json_data or "800" in json_data


class TestRecurringRuleSchema:
    """Test recurring-rule schema validation."""

    def test_valid_recurring_rule_defaults_interval(self):
        rule = RecurringRuleCreate(
            description="Gym",
            amount=Decimal("25.00"),
            type="expense",
            frequency="daily",
            start_date=datetime.now().date(),
            account_id=uuid4(),
        )
        assert rule.interval == 1

    def test_recurring_rule_invalid_interval(self):
        with pytest.raises(ValidationError):
            RecurringRuleCreate(
                description="Gym",
                amount=Decimal("25.00"),
                type="expense",
                frequency="daily",
                interval=0,
                start_date=datetime.now().date(),
                account_id=uuid4(),
            )

    def test_recurring_rule_update_invalid_interval(self):
        with pytest.raises(ValidationError):
            RecurringRuleUpdate(interval=0)


class TestBudgetSchema:
    def test_valid_group_budget(self):
        budget = BudgetCreate(
            name="Groceries",
            amount=Decimal("200.00"),
            period_start=datetime(2026, 3, 1).date(),
            period_end=datetime(2026, 3, 31).date(),
            scope=BudgetScope.GROUP,
            category_group_id=uuid4(),
        )
        assert budget.scope == BudgetScope.GROUP

    def test_budget_requires_matching_scope_target(self):
        with pytest.raises(ValidationError):
            BudgetCreate(
                name="Broken",
                amount=Decimal("200.00"),
                period_start=datetime(2026, 3, 1).date(),
                period_end=datetime(2026, 3, 31).date(),
                scope=BudgetScope.CATEGORY,
                category_group_id=uuid4(),
            )

    def test_clone_budget_requires_valid_period(self):
        with pytest.raises(ValidationError):
            BudgetCloneCreate(
                period_start=datetime(2026, 4, 30).date(),
                period_end=datetime(2026, 4, 1).date(),
            )
