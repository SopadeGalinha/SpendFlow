"""Tests for account management and soft delete functionality."""

from decimal import Decimal
from uuid import uuid4

from fastapi import status

from src.models import Account


def test_create_account(client, test_user, test_user_object):
    """Test account creation with valid data."""
    response = client.post(
        "/api/v1/accounts/accounts",
        headers={"Authorization": f"Bearer {test_user}"},
        json={
            "name": "Checking Account",
            "balance": "1000.50",
        },
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["name"] == "Checking Account"
    assert data["balance"] == "1000.50"


def test_list_accounts(
    client, test_user, test_user_object, session, event_loop
):
    """Test listing user's accounts."""

    async def setup():
        account1 = Account(
            name="Account 1",
            balance=Decimal("100.00"),
            user_id=test_user_object.id,
        )
        account2 = Account(
            name="Account 2",
            balance=Decimal("200.00"),
            user_id=test_user_object.id,
        )
        session.add(account1)
        session.add(account2)
        await session.commit()

    event_loop.run_until_complete(setup())

    response = client.get(
        "/api/v1/accounts/accounts",
        headers={"Authorization": f"Bearer {test_user}"},
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 2


def test_get_account(client, test_user, test_user_object, session, event_loop):
    """Test retrieving a specific account."""

    async def setup():
        account = Account(
            name="Test Account",
            balance=Decimal("500.00"),
            user_id=test_user_object.id,
        )
        session.add(account)
        await session.commit()
        await session.refresh(account)
        return account

    account = event_loop.run_until_complete(setup())

    response = client.get(
        f"/api/v1/accounts/accounts/{account.id}",
        headers={"Authorization": f"Bearer {test_user}"},
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["name"] == "Test Account"
    assert data["balance"] == "500.00"


def test_update_account(
    client, test_user, test_user_object, session, event_loop
):
    """Test updating an existing account."""

    async def setup():
        account = Account(
            name="Old Name",
            balance=Decimal("100.00"),
            user_id=test_user_object.id,
        )
        session.add(account)
        await session.commit()
        await session.refresh(account)
        return account

    account = event_loop.run_until_complete(setup())

    response = client.put(
        f"/api/v1/accounts/accounts/{account.id}",
        headers={"Authorization": f"Bearer {test_user}"},
        json={
            "name": "New Name",
            "balance": "250.00",
        },
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["name"] == "New Name"
    assert data["balance"] == "250.00"


def test_delete_account_soft_delete(
    client, test_user, test_user_object, session, event_loop
):
    """Test soft delete functionality."""

    async def setup():
        account = Account(
            name="To Delete",
            balance=Decimal("500.00"),
            user_id=test_user_object.id,
        )
        session.add(account)
        await session.commit()
        await session.refresh(account)
        return account

    account = event_loop.run_until_complete(setup())
    account_id = account.id

    assert account.deleted_at is None

    response = client.delete(
        f"/api/v1/accounts/accounts/{account_id}",
        headers={"Authorization": f"Bearer {test_user}"},
    )
    assert response.status_code == status.HTTP_204_NO_CONTENT

    # Query the account fresh to verify deletion
    async def check_deleted():
        from sqlalchemy import select

        stmt = select(Account).where(Account.id == account_id)
        result = await session.execute(stmt)
        updated_account = result.scalar_one_or_none()
        return updated_account

    updated_account = event_loop.run_until_complete(check_deleted())
    assert updated_account is not None
    assert updated_account.deleted_at is not None


def test_deleted_account_not_listed(
    client, test_user, test_user_object, session, event_loop
):
    """Test that deleted accounts don't appear in list."""

    async def setup():
        account = Account(
            name="Deleted Account",
            balance=Decimal("100.00"),
            user_id=test_user_object.id,
        )
        session.add(account)
        await session.commit()
        await session.refresh(account)
        return account

    account = event_loop.run_until_complete(setup())

    client.delete(
        f"/api/v1/accounts/accounts/{account.id}",
        headers={"Authorization": f"Bearer {test_user}"},
    )

    response = client.get(
        "/api/v1/accounts/accounts",
        headers={"Authorization": f"Bearer {test_user}"},
    )
    data = response.json()
    assert len(data) == 0


def test_restore_account(
    client, test_user, test_user_object, session, event_loop
):
    """Test restoring a soft-deleted account."""

    async def setup():
        account = Account(
            name="Will Restore",
            balance=Decimal("100.00"),
            user_id=test_user_object.id,
        )
        session.add(account)
        await session.commit()
        await session.refresh(account)
        return account

    account = event_loop.run_until_complete(setup())
    account_id = account.id

    client.delete(
        f"/api/v1/accounts/accounts/{account_id}",
        headers={"Authorization": f"Bearer {test_user}"},
    )

    response = client.post(
        f"/api/v1/accounts/accounts/{account_id}/restore",
        headers={"Authorization": f"Bearer {test_user}"},
    )
    assert response.status_code == status.HTTP_200_OK

    # Query the account fresh to verify restoration
    async def check_restored():
        from sqlalchemy import select

        stmt = select(Account).where(Account.id == account_id)
        result = await session.execute(stmt)
        updated_account = result.scalar_one_or_none()
        return updated_account

    updated_account = event_loop.run_until_complete(check_restored())
    assert updated_account is not None
    assert updated_account.deleted_at is None


def test_cannot_access_other_user_account(
    client, test_user, test_user_object, session, event_loop
):
    """Test that users cannot access other user's accounts."""

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
        f"/api/v1/accounts/accounts/{account.id}",
        headers={"Authorization": f"Bearer {test_user}"},
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_account_name_validation(client, test_user):
    """Test that account name validation works."""
    response = client.post(
        "/api/v1/accounts/accounts",
        headers={"Authorization": f"Bearer {test_user}"},
        json={
            "name": "",
            "balance": "100.00",
        },
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_account_balance_cannot_be_negative(client, test_user):
    """Test that account balance validation works."""
    response = client.post(
        "/api/v1/accounts/accounts",
        headers={"Authorization": f"Bearer {test_user}"},
        json={
            "name": "Test",
            "balance": "-100.00",
        },
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
