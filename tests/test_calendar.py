"""Tests for calendar projection functionality."""

from datetime import date, datetime, timezone
from decimal import Decimal
from uuid import uuid4

from fastapi import status

from src.models import Account, RecurringRule
from src.models.enums import Frequency, TransactionType


def test_get_projection_empty_rules(
    client, test_user, test_user_object, session, event_loop
):
    """Test projection with no recurring rules."""

    async def setup():
        account = Account(
            name="Test Account",
            balance=Decimal("1000.00"),
            user_id=test_user_object.id,
        )
        session.add(account)
        await session.commit()
        await session.refresh(account)
        return account

    account = event_loop.run_until_complete(setup())

    response = client.get(
        "/api/v1/calendar/projection",
        params={
            "account_id": str(account.id),
            "month": 3,
            "year": 2026,
        },
        headers={"Authorization": f"Bearer {test_user}"},
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 0


def test_get_projection_with_monthly_rule(
    client, test_user, test_user_object, session, event_loop
):
    """Test projection with a monthly recurring rule."""

    async def setup():
        account = Account(
            name="Test Account",
            balance=Decimal("1000.00"),
            user_id=test_user_object.id,
        )
        session.add(account)
        await session.commit()
        await session.refresh(account)

        rule = RecurringRule(
            description="Monthly salary",
            amount=Decimal("2000.00"),
            type=TransactionType.INCOME,
            frequency=Frequency.MONTHLY,
            start_date=date(2026, 1, 1),
            end_date=None,
            account_id=account.id,
        )
        session.add(rule)
        await session.commit()

        return account

    account = event_loop.run_until_complete(setup())

    response = client.get(
        "/api/v1/calendar/projection",
        params={
            "account_id": str(account.id),
            "month": 3,
            "year": 2026,
        },
        headers={"Authorization": f"Bearer {test_user}"},
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 1
    assert data[0]["description"] == "Monthly salary"
    assert data[0]["amount"] == "2000.00"
    assert data[0]["type"] == "income"
    assert data[0]["balance_delta"] == "2000.00"
    assert data[0]["projected_balance"] == "3000.00"


def test_get_projection_invalid_month(client, test_user):
    """Test projection with invalid month."""
    response = client.get(
        "/api/v1/calendar/projection",
        params={
            "account_id": str(uuid4()),
            "month": 13,
            "year": 2026,
        },
        headers={"Authorization": f"Bearer {test_user}"},
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_get_projection_invalid_year(client, test_user):
    """Test projection with invalid year."""
    response = client.get(
        "/api/v1/calendar/projection",
        params={
            "account_id": str(uuid4()),
            "month": 3,
            "year": 2000,
        },
        headers={"Authorization": f"Bearer {test_user}"},
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_get_projection_unauthorized_account(
    client, test_user, session, event_loop
):
    """Test that users cannot project other user's account."""

    async def setup():
        other_user_id = uuid4()
        account = Account(
            name="Other User Account",
            balance=Decimal("1000.00"),
            user_id=other_user_id,
        )
        session.add(account)
        await session.commit()
        await session.refresh(account)
        return account

    account = event_loop.run_until_complete(setup())

    response = client.get(
        "/api/v1/calendar/projection",
        params={
            "account_id": str(account.id),
            "month": 3,
            "year": 2026,
        },
        headers={"Authorization": f"Bearer {test_user}"},
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_get_projection_nonexistent_account(client, test_user):
    """Test projection with non-existent account."""
    response = client.get(
        "/api/v1/calendar/projection",
        params={
            "account_id": str(uuid4()),
            "month": 3,
            "year": 2026,
        },
        headers={"Authorization": f"Bearer {test_user}"},
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_get_projection_deleted_account(
    client, test_user, test_user_object, session, event_loop
):
    """Test that projection unavailable for deleted accounts."""

    async def setup():
        account = Account(
            name="Deleted Account",
            balance=Decimal("1000.00"),
            user_id=test_user_object.id,
        )
        session.add(account)
        await session.commit()
        await session.refresh(account)

        account.deleted_at = datetime.now(timezone.utc)
        session.add(account)
        await session.commit()

        return account

    account = event_loop.run_until_complete(setup())

    response = client.get(
        "/api/v1/calendar/projection",
        params={
            "account_id": str(account.id),
            "month": 3,
            "year": 2026,
        },
        headers={"Authorization": f"Bearer {test_user}"},
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_get_projection_multiple_rules(
    client, test_user, test_user_object, session, event_loop
):
    """Test projection with multiple recurring rules."""

    async def setup():
        account = Account(
            name="Test Account",
            balance=Decimal("1000.00"),
            user_id=test_user_object.id,
        )
        session.add(account)
        await session.commit()
        await session.refresh(account)

        rule1 = RecurringRule(
            description="Monthly salary",
            amount=Decimal("2000.00"),
            type=TransactionType.INCOME,
            frequency=Frequency.MONTHLY,
            start_date=date(2026, 1, 1),
            account_id=account.id,
        )
        rule2 = RecurringRule(
            description="Monthly rent",
            amount=Decimal("800.00"),
            type=TransactionType.EXPENSE,
            frequency=Frequency.MONTHLY,
            start_date=date(2026, 1, 5),
            account_id=account.id,
        )
        session.add(rule1)
        session.add(rule2)
        await session.commit()

        return account

    account = event_loop.run_until_complete(setup())

    response = client.get(
        "/api/v1/calendar/projection",
        params={
            "account_id": str(account.id),
            "month": 3,
            "year": 2026,
        },
        headers={"Authorization": f"Bearer {test_user}"},
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 2
    assert data[0]["description"] == "Monthly salary"
    assert data[0]["projected_balance"] == "3000.00"
    assert data[1]["description"] == "Monthly rent"
    assert data[1]["amount"] == "800.00"
    assert data[1]["balance_delta"] == "-800.00"
    assert data[1]["projected_balance"] == "2200.00"
