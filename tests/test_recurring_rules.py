"""Tests for recurring rule CRUD endpoints."""

from datetime import date
from decimal import Decimal
from uuid import uuid4

from fastapi import status
from sqlalchemy import select

from src.models import Account, RecurringRule, User


async def _create_account(session, user_id, balance="1000.00"):
    account = Account(
        name="Recurring Account",
        balance=Decimal(balance),
        user_id=user_id,
    )
    session.add(account)
    await session.commit()
    await session.refresh(account)
    return account


def test_create_weekly_recurring_expense(
    client, test_user, test_user_object, session, event_loop
):
    account = event_loop.run_until_complete(
        _create_account(session, test_user_object.id)
    )

    response = client.post(
        "/api/v1/calendar/rules",
        headers={"Authorization": f"Bearer {test_user}"},
        json={
            "description": "Gym",
            "amount": "25.00",
            "type": "expense",
            "frequency": "weekly",
            "interval": 2,
            "start_date": "2026-03-01",
            "weekend_adjustment": "keep",
            "account_id": str(account.id),
        },
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["description"] == "Gym"
    assert data["amount"] == "25.00"
    assert data["type"] == "expense"
    assert data["frequency"] == "weekly"
    assert data["interval"] == 2


def test_list_recurring_rules(
    client, test_user, test_user_object, session, event_loop
):
    async def setup():
        account = await _create_account(session, test_user_object.id)
        session.add(
            RecurringRule(
                description="Salary",
                amount=Decimal("1000.00"),
                type="income",
                frequency="monthly",
                interval=1,
                start_date=date(2026, 3, 1),
                account_id=account.id,
            )
        )
        await session.commit()
        return account

    account = event_loop.run_until_complete(setup())

    response = client.get(
        "/api/v1/calendar/rules",
        headers={"Authorization": f"Bearer {test_user}"},
        params={"account_id": str(account.id)},
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 1
    assert data[0]["description"] == "Salary"
    assert data[0]["interval"] == 1


def test_update_recurring_rule_normalizes_amount(
    client, test_user, test_user_object, session, event_loop
):
    async def setup():
        account = await _create_account(session, test_user_object.id)
        rule = RecurringRule(
            description="Rent",
            amount=Decimal("800.00"),
            type="expense",
            frequency="monthly",
            interval=1,
            start_date=date(2026, 3, 5),
            account_id=account.id,
        )
        session.add(rule)
        await session.commit()
        await session.refresh(rule)
        return rule

    rule = event_loop.run_until_complete(setup())

    response = client.put(
        f"/api/v1/calendar/rules/{rule.id}",
        headers={"Authorization": f"Bearer {test_user}"},
        json={
            "amount": "900.00",
            "frequency": "monthly",
            "interval": 15,
            "end_date": "2026-12-05",
        },
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["amount"] == "900.00"
    assert data["interval"] == 15
    assert data["end_date"] == "2026-12-05"


def test_delete_recurring_rule_soft_delete(
    client, test_user, test_user_object, session, event_loop
):
    async def setup():
        account = await _create_account(session, test_user_object.id)
        rule = RecurringRule(
            description="Internet",
            amount=Decimal("60.00"),
            type="expense",
            frequency="monthly",
            interval=1,
            start_date=date(2026, 3, 10),
            account_id=account.id,
        )
        session.add(rule)
        await session.commit()
        await session.refresh(rule)
        return rule

    rule = event_loop.run_until_complete(setup())

    response = client.delete(
        f"/api/v1/calendar/rules/{rule.id}",
        headers={"Authorization": f"Bearer {test_user}"},
    )
    assert response.status_code == status.HTTP_204_NO_CONTENT

    async def fetch_rule():
        stmt = select(RecurringRule).where(RecurringRule.id == rule.id)
        result = await session.execute(stmt)
        return result.scalar_one()

    deleted_rule = event_loop.run_until_complete(fetch_rule())
    assert deleted_rule.deleted_at is not None


def test_cannot_create_rule_on_other_user_account(
    client, test_user, session, event_loop
):
    async def setup():
        other_user = User(
            id=uuid4(),
            username="other_recurring_owner",
            email="other_recurring_owner@example.com",
            hashed_password="placeholder",
            timezone="UTC",
            currency="USD",
        )
        session.add(other_user)
        await session.commit()
        return await _create_account(session, other_user.id)

    account = event_loop.run_until_complete(setup())

    response = client.post(
        "/api/v1/calendar/rules",
        headers={"Authorization": f"Bearer {test_user}"},
        json={
            "description": "Unauthorized rule",
            "amount": "20.00",
            "type": "expense",
            "frequency": "weekly",
            "start_date": "2026-03-01",
            "account_id": str(account.id),
        },
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_rejects_invalid_recurring_rule_date_range(
    client, test_user, test_user_object, session, event_loop
):
    account = event_loop.run_until_complete(
        _create_account(session, test_user_object.id)
    )

    response = client.post(
        "/api/v1/calendar/rules",
        headers={"Authorization": f"Bearer {test_user}"},
        json={
            "description": "Broken rule",
            "amount": "30.00",
            "type": "expense",
            "frequency": "monthly",
            "start_date": "2026-04-01",
            "end_date": "2026-03-01",
            "account_id": str(account.id),
        },
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_create_recurring_rule_rejects_zero_interval(
    client, test_user, test_user_object, session, event_loop
):
    account = event_loop.run_until_complete(
        _create_account(session, test_user_object.id)
    )

    response = client.post(
        "/api/v1/calendar/rules",
        headers={"Authorization": f"Bearer {test_user}"},
        json={
            "description": "Broken schedule",
            "amount": "25.00",
            "type": "expense",
            "frequency": "daily",
            "interval": 0,
            "start_date": "2026-03-01",
            "account_id": str(account.id),
        },
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_create_recurring_rule_rejects_negative_amount(
    client, test_user, test_user_object, session, event_loop
):
    account = event_loop.run_until_complete(
        _create_account(session, test_user_object.id)
    )

    response = client.post(
        "/api/v1/calendar/rules",
        headers={"Authorization": f"Bearer {test_user}"},
        json={
            "description": "Invalid recurring expense",
            "amount": "-25.00",
            "type": "expense",
            "frequency": "weekly",
            "start_date": "2026-03-01",
            "account_id": str(account.id),
        },
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
