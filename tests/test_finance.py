"""Tests for account management and soft delete functionality."""

from decimal import Decimal
from uuid import UUID, uuid4

from fastapi import status
from sqlalchemy import select

from src.models import Account, Transaction, TransactionKind


def test_create_account(client, test_user):
    response = client.post(
        "/api/v1/accounts",
        headers={"Authorization": f"Bearer {test_user}"},
        json={
            "name": "Checking Account",
            "account_type": "checking",
            "opening_balance": "1000.50",
        },
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["name"] == "Checking Account"
    assert data["account_type"] == "checking"
    assert data["balance"] == "1000.50"


def test_create_account_writes_opening_balance_entry(
    client, test_user, session, event_loop
):
    response = client.post(
        "/api/v1/accounts",
        headers={"Authorization": f"Bearer {test_user}"},
        json={
            "name": "Seeded Account",
            "opening_balance": "500.00",
        },
    )
    account_id = UUID(response.json()["id"])

    async def load_transactions():
        stmt = select(Transaction).where(Transaction.account_id == account_id)
        result = await session.execute(stmt)
        return list(result.scalars().all())

    transactions = event_loop.run_until_complete(load_transactions())
    assert len(transactions) == 1
    assert transactions[0].kind == TransactionKind.OPENING_BALANCE
    assert transactions[0].amount == Decimal("500.00")


def test_list_accounts(
    client, test_user, test_user_object, session, event_loop
):
    async def setup():
        session.add(
            Account(
                name="Account 1",
                balance=Decimal("100.00"),
                user_id=test_user_object.id,
            )
        )
        session.add(
            Account(
                name="Account 2",
                balance=Decimal("200.00"),
                user_id=test_user_object.id,
            )
        )
        await session.commit()

    event_loop.run_until_complete(setup())

    response = client.get(
        "/api/v1/accounts",
        headers={"Authorization": f"Bearer {test_user}"},
    )
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 2


def test_get_account(client, test_user, test_user_object, session, event_loop):
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
        f"/api/v1/accounts/{account.id}",
        headers={"Authorization": f"Bearer {test_user}"},
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["name"] == "Test Account"
    assert data["balance"] == "500.00"


def test_update_account_name_and_type(
    client, test_user, test_user_object, session, event_loop
):
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
        f"/api/v1/accounts/{account.id}",
        headers={"Authorization": f"Bearer {test_user}"},
        json={
            "name": "New Name",
            "account_type": "savings",
        },
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["name"] == "New Name"
    assert data["account_type"] == "savings"
    assert data["balance"] == "100.00"


def test_delete_account_soft_delete(
    client, test_user, test_user_object, session, event_loop
):
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

    response = client.delete(
        f"/api/v1/accounts/{account.id}",
        headers={"Authorization": f"Bearer {test_user}"},
    )
    assert response.status_code == status.HTTP_204_NO_CONTENT

    async def check_deleted():
        stmt = select(Account).where(Account.id == account.id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    updated_account = event_loop.run_until_complete(check_deleted())
    assert updated_account is not None
    assert updated_account.deleted_at is not None


def test_deleted_account_not_listed(
    client, test_user, test_user_object, session, event_loop
):
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
        f"/api/v1/accounts/{account.id}",
        headers={"Authorization": f"Bearer {test_user}"},
    )

    response = client.get(
        "/api/v1/accounts",
        headers={"Authorization": f"Bearer {test_user}"},
    )
    assert len(response.json()) == 0


def test_restore_account(
    client, test_user, test_user_object, session, event_loop
):
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

    client.delete(
        f"/api/v1/accounts/{account.id}",
        headers={"Authorization": f"Bearer {test_user}"},
    )

    response = client.post(
        f"/api/v1/accounts/{account.id}/restore",
        headers={"Authorization": f"Bearer {test_user}"},
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["id"] == str(account.id)
    assert response.json()["balance"] == "100.00"


def test_cannot_access_other_user_account(
    client, test_user, session, event_loop
):
    async def setup():
        account = Account(
            name="Other User Account",
            balance=Decimal("1000.00"),
            user_id=uuid4(),
        )
        session.add(account)
        await session.commit()
        await session.refresh(account)
        return account

    account = event_loop.run_until_complete(setup())

    response = client.get(
        f"/api/v1/accounts/{account.id}",
        headers={"Authorization": f"Bearer {test_user}"},
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_account_name_validation(client, test_user):
    response = client.post(
        "/api/v1/accounts",
        headers={"Authorization": f"Bearer {test_user}"},
        json={
            "name": "",
            "opening_balance": "100.00",
        },
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_account_opening_balance_cannot_be_negative(client, test_user):
    response = client.post(
        "/api/v1/accounts",
        headers={"Authorization": f"Bearer {test_user}"},
        json={
            "name": "Test",
            "opening_balance": "-100.00",
        },
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
