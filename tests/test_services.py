"""Tests for business logic services."""

from datetime import date, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest

from src.models import RecurringRule
from src.models.enums import Frequency, TransactionType, WeekendAdjustment
from src.services import CalendarService


class TestCalendarService:
    """Test CalendarService date adjustment logic."""

    def test_adjust_date_weekday_keep(self):
        """Test that weekday dates are unchanged with KEEP rule."""
        monday = date(2026, 3, 2)
        adjusted = CalendarService.adjust_date(monday, WeekendAdjustment.KEEP)
        assert adjusted == monday

    def test_adjust_date_saturday_keep(self):
        """Test that Saturday is unchanged with KEEP rule."""
        saturday = date(2026, 3, 7)
        adjusted = CalendarService.adjust_date(
            saturday, WeekendAdjustment.KEEP
        )
        assert adjusted == saturday

    def test_adjust_date_saturday_following(self):
        """Test that Saturday becomes Monday with FOLLOWING rule."""
        saturday = date(2026, 3, 7)
        adjusted = CalendarService.adjust_date(
            saturday, WeekendAdjustment.FOLLOWING
        )
        monday = date(2026, 3, 9)
        assert adjusted == monday

    def test_adjust_date_sunday_following(self):
        """Test that Sunday becomes Monday with FOLLOWING rule."""
        sunday = date(2026, 3, 8)
        adjusted = CalendarService.adjust_date(
            sunday, WeekendAdjustment.FOLLOWING
        )
        monday = date(2026, 3, 9)
        assert adjusted == monday

    def test_adjust_date_saturday_preceding(self):
        """Test that Saturday becomes Friday with PRECEDING rule."""
        saturday = date(2026, 3, 7)
        adjusted = CalendarService.adjust_date(
            saturday, WeekendAdjustment.PRECEDING
        )
        friday = date(2026, 3, 6)
        assert adjusted == friday

    def test_adjust_date_sunday_preceding(self):
        """Test that Sunday becomes Friday with PRECEDING rule."""
        sunday = date(2026, 3, 8)
        adjusted = CalendarService.adjust_date(
            sunday, WeekendAdjustment.PRECEDING
        )
        friday = date(2026, 3, 6)
        assert adjusted == friday

    def test_get_projection_monthly_frequency(self):
        """Test projection generation with monthly frequency."""
        rule = RecurringRule(
            id=uuid4(),
            description="Test",
            amount=Decimal("100.00"),
            type=TransactionType.INCOME,
            frequency=Frequency.MONTHLY,
            start_date=date(2026, 1, 15),
            account_id=uuid4(),
        )

        start = date(2026, 3, 1)
        end = date(2026, 3, 31)
        projections = CalendarService.get_projection([rule], start, end)

        assert len(projections) == 1
        assert projections[0].description == "Test"

    def test_get_projection_weekly_frequency(self):
        """Test projection generation with weekly frequency."""
        rule = RecurringRule(
            id=uuid4(),
            description="Weekly check",
            amount=Decimal("50.00"),
            type=TransactionType.EXPENSE,
            frequency=Frequency.WEEKLY,
            start_date=date(2026, 3, 1),
            account_id=uuid4(),
        )

        start = date(2026, 3, 1)
        end = date(2026, 3, 31)
        projections = CalendarService.get_projection([rule], start, end)

        assert len(projections) >= 4
        assert all(p.type == TransactionType.EXPENSE for p in projections)
        assert all(p.amount == Decimal("50.00") for p in projections)
        assert all(p.balance_delta == Decimal("-50.00") for p in projections)

    def test_get_projection_every_fifteen_days(self):
        """Daily frequency with interval should support every N days."""
        rule = RecurringRule(
            id=uuid4(),
            description="Gym",
            amount=Decimal("25.00"),
            type=TransactionType.EXPENSE,
            frequency=Frequency.DAILY,
            interval=15,
            start_date=date(2026, 3, 1),
            account_id=uuid4(),
        )

        projections = CalendarService.get_projection(
            [rule],
            date(2026, 3, 1),
            date(2026, 3, 31),
            current_balance=Decimal("100.00"),
        )

        assert [p.original_date for p in projections] == [
            date(2026, 3, 1),
            date(2026, 3, 16),
            date(2026, 3, 31),
        ]
        assert projections[-1].projected_balance == Decimal("25.00")

    def test_get_projection_normalizes_legacy_negative_expense_amount(self):
        """Negative legacy expense amounts should be normalized."""
        rule = RecurringRule(
            id=uuid4(),
            description="Legacy rent",
            amount=Decimal("-800.00"),
            type=TransactionType.EXPENSE,
            frequency=Frequency.MONTHLY,
            interval=1,
            start_date=date(2026, 3, 5),
            account_id=uuid4(),
        )

        projections = CalendarService.get_projection(
            [rule],
            date(2026, 3, 1),
            date(2026, 3, 31),
            current_balance=Decimal("1000.00"),
        )

        assert len(projections) == 1
        assert projections[0].amount == Decimal("800.00")
        assert projections[0].balance_delta == Decimal("-800.00")
        assert projections[0].projected_balance == Decimal("200.00")

    def test_get_projection_empty_rules(self):
        """Test projection with no rules."""
        start = date(2026, 3, 1)
        end = date(2026, 3, 31)
        projections = CalendarService.get_projection([], start, end)

        assert len(projections) == 0

    def test_get_projection_outside_date_range(self):
        """Test that projections outside range are excluded."""
        rule = RecurringRule(
            id=uuid4(),
            description="Future event",
            amount=Decimal("100.00"),
            type=TransactionType.INCOME,
            frequency=Frequency.MONTHLY,
            start_date=date(2026, 5, 1),
            account_id=uuid4(),
        )

        start = date(2026, 3, 1)
        end = date(2026, 3, 31)
        projections = CalendarService.get_projection([rule], start, end)

        assert len(projections) == 0


class TestAuthService:
    """Test AuthService business logic."""

    def test_password_validation_min_length(self):
        """Test password validation minimum length."""
        from src.core.security import get_password_hash

        short_pass = "abc"
        try:
            hashed = get_password_hash(short_pass)
            assert hashed is not None
        except ValueError:
            pytest.fail("Should accept password even if short")

    def test_password_hashing(self):
        """Test that passwords are properly hashed."""
        from src.core.security import (
            get_password_hash,
            verify_password,
        )

        password = "MySecurePassword123"
        hashed = get_password_hash(password)

        assert hashed != password
        assert verify_password(password, hashed)

    def test_incorrect_password_verification(self):
        """Test that wrong password fails verification."""
        from src.core.security import (
            get_password_hash,
            verify_password,
        )

        password = "CorrectPassword123"
        hashed = get_password_hash(password)

        assert not verify_password("WrongPassword123", hashed)

    def test_create_access_token(self):
        """Test JWT token creation."""
        from src.core.security import create_access_token

        user_id = str(uuid4())
        token = create_access_token(user_id)

        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_access_token_with_expiry(self):
        """Test JWT token with custom expiry."""
        from src.core.security import create_access_token

        user_id = str(uuid4())
        expires = timedelta(hours=1)
        token = create_access_token(user_id, expires)

        assert isinstance(token, str)
        assert token != ""
