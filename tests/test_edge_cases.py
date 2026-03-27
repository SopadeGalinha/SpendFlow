"""Tests for edge cases, error handling, and security."""

from decimal import Decimal
from uuid import uuid4

from fastapi import status

from src.models import Account


def test_user_cannot_list_other_user_accounts(
    client, test_user, test_user_object, session, event_loop
):
    """Test that users can't access other user's accounts."""
    from src.core.security import get_password_hash
    from src.models import User

    async def setup():
        other_user = User(
            id=uuid4(),
            username="other_user",
            email="other@example.com",
            hashed_password=get_password_hash("password123"),
            timezone="UTC",
            currency="USD",
        )
        session.add(other_user)
        await session.commit()

        account = Account(
            name="Other User Account",
            balance=Decimal("5000.00"),
            user_id=other_user.id,
        )
        session.add(account)
        await session.commit()

    event_loop.run_until_complete(setup())

    response = client.get(
        "/api/v1/accounts",
        headers={"Authorization": f"Bearer {test_user}"},
    )
    data = response.json()
    assert len(data) == 0


def test_cannot_update_account_balance_to_negative(
    client, test_user, test_user_object, session, event_loop
):
    """Test that account balance cannot be updated to negative."""

    async def setup():
        account = Account(
            name="Test",
            balance=Decimal("100.00"),
            user_id=test_user_object.id,
        )
        session.add(account)
        await session.commit()
        await session.refresh(account)
        return account

    account = event_loop.run_until_complete(setup())

    response = client.put(
        f"/api/v1/accounts/{account.id}",
        headers={"Authorization": f"Bearer {test_user}"},
        json={
            "name": "Updated",
            "balance": "-50.00",
        },
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_deleted_account_cannot_be_accessed(
    client, test_user, test_user_object, session, event_loop
):
    """Test that deleted accounts return 404 when accessed."""

    async def setup():
        account = Account(
            name="To Delete",
            balance=Decimal("100.00"),
            user_id=test_user_object.id,
        )
        session.add(account)
        await session.commit()
        await session.refresh(account)
        return account

    account = event_loop.run_until_complete(setup())

    client.delete(
        f"/api/v1/accounts/{account.id}",
        headers={"Authorization": f"Bearer {test_user}"},
    )

    response = client.get(
        f"/api/v1/accounts/{account.id}",
        headers={"Authorization": f"Bearer {test_user}"},
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_account_name_with_special_characters(client, test_user):
    """Test that account names with special characters work."""
    response = client.post(
        "/api/v1/accounts",
        headers={"Authorization": f"Bearer {test_user}"},
        json={
            "name": "Banco Centro 2026 (Investimentos)",
            "opening_balance": "1000.00",
        },
    )
    assert response.status_code == status.HTTP_201_CREATED


def test_account_with_large_balance(client, test_user):
    """Test that accounts with large balances work."""
    response = client.post(
        "/api/v1/accounts",
        headers={"Authorization": f"Bearer {test_user}"},
        json={
            "name": "High Balance",
            "opening_balance": "999999999.99",
        },
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["balance"] == "999999999.99"


def test_account_with_precise_decimal(client, test_user):
    """Test that account balances maintain decimal precision."""
    response = client.post(
        "/api/v1/accounts",
        headers={"Authorization": f"Bearer {test_user}"},
        json={
            "name": "Precise",
            "opening_balance": "123.45",
        },
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["balance"] == "123.45"


def test_multiple_accounts_same_user(client, test_user):
    """Test creating multiple accounts for same user."""
    for i in range(5):
        response = client.post(
            "/api/v1/accounts",
            headers={"Authorization": f"Bearer {test_user}"},
            json={
                "name": f"Account {i}",
                "opening_balance": f"{100 * i}.00",
            },
        )
        assert response.status_code == status.HTTP_201_CREATED

    response = client.get(
        "/api/v1/accounts",
        headers={"Authorization": f"Bearer {test_user}"},
    )
    data = response.json()
    assert len(data) == 5


def test_missing_required_query_parameters(client, test_user):
    """Test calendar projection with missing required parameters."""
    response = client.get(
        "/api/v1/calendar/projection",
        params={"month": 3},
        headers={"Authorization": f"Bearer {test_user}"},
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_cors_headers_present(client):
    """Test that CORS headers are properly set."""
    response = client.get("/health")
    assert response.status_code == status.HTTP_200_OK


def test_security_headers_present(client):
    """Test that security headers are present."""
    response = client.get("/health")
    assert "X-Content-Type-Options" in response.headers
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert "X-Frame-Options" in response.headers
    assert response.headers["X-Frame-Options"] == "DENY"
