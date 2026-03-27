"""Tests for persisted transactions endpoints and balance updates."""

from datetime import date
from decimal import Decimal
from uuid import UUID, uuid4

from fastapi import status
from sqlalchemy import select

from src.models import (
    Account,
    Transaction,
    TransactionType,
    User,
)


async def _create_account(session, user_id, balance="1000.00"):
    account = Account(
        name="Primary Account",
        balance=Decimal(balance),
        user_id=user_id,
    )
    session.add(account)
    await session.commit()
    await session.refresh(account)
    return account


async def _get_account(session, account_id):
    stmt = select(Account).where(Account.id == account_id)
    result = await session.execute(stmt)
    return result.scalar_one()


async def _get_transaction(session, transaction_id):
    stmt = select(Transaction).where(Transaction.id == transaction_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


def _get_category_id(client, token, slug, category_type):
    response = client.get(
        "/api/v1/categories",
        headers={"Authorization": f"Bearer {token}"},
        params={"type": category_type},
    )
    assert response.status_code == status.HTTP_200_OK
    for category in response.json():
        if category["slug"] == slug:
            return category["id"]
    raise AssertionError(f"Category '{slug}' not found")


def test_create_income_transaction(
    client, test_user, test_user_object, session, event_loop
):
    account = event_loop.run_until_complete(
        _create_account(session, test_user_object.id)
    )
    salary_category_id = _get_category_id(
        client,
        test_user,
        "salary",
        "income",
    )

    response = client.post(
        "/api/v1/transactions",
        headers={"Authorization": f"Bearer {test_user}"},
        json={
            "description": "Salary",
            "amount": "250.00",
            "type": "income",
            "transaction_date": "2026-03-25",
            "account_id": str(account.id),
            "category_id": salary_category_id,
        },
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["type"] == "income"
    assert data["kind"] == "regular"
    assert data["amount"] == "250.00"
    assert data["category_id"] == salary_category_id

    updated_account = event_loop.run_until_complete(
        _get_account(session, account.id)
    )
    assert updated_account.balance == Decimal("1250.00")


def test_create_expense_transaction(
    client, test_user, test_user_object, session, event_loop
):
    account = event_loop.run_until_complete(
        _create_account(session, test_user_object.id)
    )
    groceries_category_id = _get_category_id(
        client,
        test_user,
        "groceries",
        "expense",
    )

    response = client.post(
        "/api/v1/transactions",
        headers={"Authorization": f"Bearer {test_user}"},
        json={
            "description": "Groceries",
            "amount": "125.00",
            "type": "expense",
            "transaction_date": "2026-03-25",
            "account_id": str(account.id),
            "category_id": groceries_category_id,
        },
    )
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["kind"] == "regular"

    updated_account = event_loop.run_until_complete(
        _get_account(session, account.id)
    )
    assert updated_account.balance == Decimal("875.00")


def test_create_transfer_between_accounts(
    client, test_user, test_user_object, session, event_loop
):
    source_account = event_loop.run_until_complete(
        _create_account(session, test_user_object.id, balance="1000.00")
    )
    destination_account = event_loop.run_until_complete(
        _create_account(session, test_user_object.id, balance="300.00")
    )

    response = client.post(
        "/api/v1/transactions/transfers",
        headers={"Authorization": f"Bearer {test_user}"},
        json={
            "description": "Move cash",
            "amount": "50.00",
            "transaction_date": "2026-03-25",
            "from_account_id": str(source_account.id),
            "to_account_id": str(destination_account.id),
        },
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["amount"] == "50.00"
    assert data["from_entry"]["kind"] == "transfer"
    assert data["from_entry"]["type"] == "expense"
    assert data["to_entry"]["kind"] == "transfer"
    assert data["to_entry"]["type"] == "income"
    assert data["from_entry"]["transfer_group_id"] == data["transfer_group_id"]
    assert data["to_entry"]["transfer_group_id"] == data["transfer_group_id"]

    updated_source = event_loop.run_until_complete(
        _get_account(session, source_account.id)
    )
    updated_destination = event_loop.run_until_complete(
        _get_account(session, destination_account.id)
    )
    assert updated_source.balance == Decimal("950.00")
    assert updated_destination.balance == Decimal("350.00")


def test_create_adjustment_entry(
    client, test_user, test_user_object, session, event_loop
):
    account = event_loop.run_until_complete(
        _create_account(session, test_user_object.id, balance="1000.00")
    )

    response = client.post(
        "/api/v1/transactions/adjustments",
        headers={"Authorization": f"Bearer {test_user}"},
        json={
            "description": "Reconciliation correction",
            "amount": "25.00",
            "type": "expense",
            "transaction_date": "2026-03-25",
            "account_id": str(account.id),
        },
    )
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["kind"] == "adjustment"

    updated_account = event_loop.run_until_complete(
        _get_account(session, account.id)
    )
    assert updated_account.balance == Decimal("975.00")


def test_create_income_legacy_alias(
    client, test_user, test_user_object, session, event_loop
):
    account = event_loop.run_until_complete(
        _create_account(session, test_user_object.id)
    )
    salary_category_id = _get_category_id(
        client,
        test_user,
        "salary",
        "income",
    )

    response = client.post(
        "/api/v1/transactions/incomes",
        headers={"Authorization": f"Bearer {test_user}"},
        json={
            "description": "Legacy salary",
            "amount": "250.00",
            "transaction_date": "2026-03-25",
            "account_id": str(account.id),
            "category_id": salary_category_id,
        },
    )
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["type"] == "income"


def test_cannot_create_transaction_on_other_user_account(
    client, test_user, session, event_loop
):
    async def setup():
        other_user = User(
            id=uuid4(),
            username="other_owner",
            email="other_owner@example.com",
            hashed_password="placeholder",
            timezone="UTC",
            currency="USD",
        )
        session.add(other_user)
        await session.commit()
        return await _create_account(session, other_user.id)

    account = event_loop.run_until_complete(setup())

    response = client.post(
        "/api/v1/transactions",
        headers={"Authorization": f"Bearer {test_user}"},
        json={
            "description": "Unauthorized",
            "amount": "50.00",
            "type": "income",
            "transaction_date": "2026-03-25",
            "account_id": str(account.id),
        },
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_list_transactions_filtered_by_type(
    client, test_user, test_user_object, session, event_loop
):
    account = event_loop.run_until_complete(
        _create_account(session, test_user_object.id)
    )
    salary_category_id = _get_category_id(
        client,
        test_user,
        "salary",
        "income",
    )
    rent_category_id = _get_category_id(
        client,
        test_user,
        "housing",
        "expense",
    )

    client.post(
        "/api/v1/transactions",
        headers={"Authorization": f"Bearer {test_user}"},
        json={
            "description": "Salary",
            "amount": "300.00",
            "type": "income",
            "transaction_date": "2026-03-01",
            "account_id": str(account.id),
            "category_id": salary_category_id,
        },
    )
    client.post(
        "/api/v1/transactions",
        headers={"Authorization": f"Bearer {test_user}"},
        json={
            "description": "Rent",
            "amount": "200.00",
            "type": "expense",
            "transaction_date": "2026-03-02",
            "account_id": str(account.id),
            "category_id": rent_category_id,
        },
    )

    response = client.get(
        "/api/v1/transactions",
        headers={"Authorization": f"Bearer {test_user}"},
        params={"type": "income"},
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 1
    assert data[0]["type"] == "income"


def test_get_transaction_requires_ownership(
    client,
    test_user,
    session,
    event_loop,
):
    async def setup():
        other_user = User(
            id=uuid4(),
            username="another_user",
            email="another_user@example.com",
            hashed_password="placeholder",
            timezone="UTC",
            currency="USD",
        )
        session.add(other_user)
        await session.commit()
        account = await _create_account(session, other_user.id)
        transaction = Transaction(
            description="Other income",
            amount=Decimal("100.00"),
            type=TransactionType.INCOME,
            transaction_date=date(2026, 3, 10),
            account_id=account.id,
        )
        session.add(transaction)
        await session.commit()
        await session.refresh(transaction)
        return transaction

    transaction = event_loop.run_until_complete(setup())

    response = client.get(
        f"/api/v1/transactions/{transaction.id}",
        headers={"Authorization": f"Bearer {test_user}"},
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_update_transaction_recalculates_balance(
    client, test_user, test_user_object, session, event_loop
):
    account = event_loop.run_until_complete(
        _create_account(session, test_user_object.id)
    )
    freelance_category_id = _get_category_id(
        client,
        test_user,
        "freelance",
        "income",
    )
    groceries_category_id = _get_category_id(
        client,
        test_user,
        "groceries",
        "expense",
    )
    create_response = client.post(
        "/api/v1/transactions",
        headers={"Authorization": f"Bearer {test_user}"},
        json={
            "description": "Freelance",
            "amount": "200.00",
            "type": "income",
            "transaction_date": "2026-03-25",
            "account_id": str(account.id),
            "category_id": freelance_category_id,
        },
    )
    transaction_id = create_response.json()["id"]

    response = client.put(
        f"/api/v1/transactions/{transaction_id}",
        headers={"Authorization": f"Bearer {test_user}"},
        json={
            "amount": "300.00",
            "type": "expense",
            "category_id": groceries_category_id,
        },
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["kind"] == "regular"

    updated_account = event_loop.run_until_complete(
        _get_account(session, account.id)
    )
    assert updated_account.balance == Decimal("700.00")


def test_delete_transaction_reverses_balance(
    client, test_user, test_user_object, session, event_loop
):
    account = event_loop.run_until_complete(
        _create_account(session, test_user_object.id)
    )
    create_response = client.post(
        "/api/v1/transactions",
        headers={"Authorization": f"Bearer {test_user}"},
        json={
            "description": "Utilities",
            "amount": "100.00",
            "type": "expense",
            "transaction_date": "2026-03-25",
            "account_id": str(account.id),
        },
    )
    transaction_id = create_response.json()["id"]

    response = client.delete(
        f"/api/v1/transactions/{transaction_id}",
        headers={"Authorization": f"Bearer {test_user}"},
    )
    assert response.status_code == status.HTTP_204_NO_CONTENT

    updated_account = event_loop.run_until_complete(
        _get_account(session, account.id)
    )
    deleted_transaction = event_loop.run_until_complete(
        _get_transaction(session, UUID(transaction_id))
    )
    assert updated_account.balance == Decimal("1000.00")
    assert deleted_transaction is not None
    assert deleted_transaction.deleted_at is not None


def test_transaction_cannot_make_balance_negative(
    client, test_user, test_user_object, session, event_loop
):
    account = event_loop.run_until_complete(
        _create_account(session, test_user_object.id, balance="50.00")
    )

    response = client.post(
        "/api/v1/transactions",
        headers={"Authorization": f"Bearer {test_user}"},
        json={
            "description": "Big purchase",
            "amount": "75.00",
            "type": "expense",
            "transaction_date": "2026-03-25",
            "account_id": str(account.id),
        },
    )
    assert response.status_code == status.HTTP_409_CONFLICT


def test_transfer_entries_cannot_be_updated_directly(
    client, test_user, test_user_object, session, event_loop
):
    source_account = event_loop.run_until_complete(
        _create_account(session, test_user_object.id, balance="1000.00")
    )
    destination_account = event_loop.run_until_complete(
        _create_account(session, test_user_object.id, balance="300.00")
    )
    transfer_response = client.post(
        "/api/v1/transactions/transfers",
        headers={"Authorization": f"Bearer {test_user}"},
        json={
            "description": "Move cash",
            "amount": "50.00",
            "transaction_date": "2026-03-25",
            "from_account_id": str(source_account.id),
            "to_account_id": str(destination_account.id),
        },
    )
    transaction_id = transfer_response.json()["from_entry"]["id"]

    response = client.put(
        f"/api/v1/transactions/{transaction_id}",
        headers={"Authorization": f"Bearer {test_user}"},
        json={"amount": "75.00"},
    )
    assert response.status_code == status.HTTP_409_CONFLICT


def test_create_transaction_rejects_negative_amount(
    client, test_user, test_user_object, session, event_loop
):
    account = event_loop.run_until_complete(
        _create_account(session, test_user_object.id)
    )

    response = client.post(
        "/api/v1/transactions",
        headers={"Authorization": f"Bearer {test_user}"},
        json={
            "description": "Invalid debit",
            "amount": "-10.00",
            "type": "expense",
            "transaction_date": "2026-03-25",
            "account_id": str(account.id),
        },
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_transaction_rejects_category_type_mismatch(
    client, test_user, test_user_object, session, event_loop
):
    account = event_loop.run_until_complete(
        _create_account(session, test_user_object.id)
    )
    groceries_category_id = _get_category_id(
        client,
        test_user,
        "groceries",
        "expense",
    )

    response = client.post(
        "/api/v1/transactions",
        headers={"Authorization": f"Bearer {test_user}"},
        json={
            "description": "Salary",
            "amount": "250.00",
            "type": "income",
            "transaction_date": "2026-03-25",
            "account_id": str(account.id),
            "category_id": groceries_category_id,
        },
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_transaction_rejects_other_user_category(
    client, test_user, test_user_object, session, event_loop
):
    async def setup():
        other_user = User(
            id=uuid4(),
            username="other_category_owner",
            email="other_category_owner@example.com",
            hashed_password="placeholder",
            timezone="UTC",
            currency="USD",
        )
        session.add(other_user)
        await session.commit()
        return other_user

    other_user = event_loop.run_until_complete(setup())
    own_account = event_loop.run_until_complete(
        _create_account(session, test_user_object.id)
    )

    from src.core.security import create_access_token

    other_token = create_access_token(str(other_user.id))
    custom_group_response = client.post(
        "/api/v1/categories/groups",
        headers={"Authorization": f"Bearer {other_token}"},
        json={"name": "Private Group", "type": "expense"},
    )
    group_id = custom_group_response.json()["id"]
    custom_category_response = client.post(
        "/api/v1/categories",
        headers={"Authorization": f"Bearer {other_token}"},
        json={
            "name": "Private Category",
            "type": "expense",
            "group_id": group_id,
        },
    )
    category_id = custom_category_response.json()["id"]

    response = client.post(
        "/api/v1/transactions",
        headers={"Authorization": f"Bearer {test_user}"},
        json={
            "description": "Blocked",
            "amount": "20.00",
            "type": "expense",
            "transaction_date": "2026-03-25",
            "account_id": str(own_account.id),
            "category_id": category_id,
        },
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
