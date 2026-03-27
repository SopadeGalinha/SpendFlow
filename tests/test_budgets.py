"""Tests for budget endpoints and calculations."""

from datetime import date, timedelta
from decimal import Decimal

from fastapi import status

from src.models import Account


async def _create_account(session, user_id, balance="1000.00"):
    account = Account(
        name="Budget Account",
        balance=Decimal(balance),
        user_id=user_id,
    )
    session.add(account)
    await session.commit()
    await session.refresh(account)
    return account


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


def _get_group_id(client, token, slug, category_type):
    response = client.get(
        "/api/v1/categories/groups",
        headers={"Authorization": f"Bearer {token}"},
        params={"type": category_type},
    )
    assert response.status_code == status.HTTP_200_OK
    for group in response.json():
        if group["slug"] == slug:
            return group["id"]
    raise AssertionError(f"Group '{slug}' not found")


def test_create_category_budget_and_calculate_spent(
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

    client.post(
        "/api/v1/transactions",
        headers={"Authorization": f"Bearer {test_user}"},
        json={
            "description": "Groceries run",
            "amount": "75.00",
            "type": "expense",
            "transaction_date": "2026-03-10",
            "account_id": str(account.id),
            "category_id": groceries_category_id,
        },
    )

    response = client.post(
        "/api/v1/budgets",
        headers={"Authorization": f"Bearer {test_user}"},
        json={
            "name": "Groceries March",
            "amount": "200.00",
            "period_start": "2026-03-01",
            "period_end": "2026-03-31",
            "scope": "category",
            "category_id": groceries_category_id,
        },
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["category_id"] == groceries_category_id
    assert data["category_name"] == "Groceries"
    assert data["category_slug"] == "groceries"
    assert data["category_group_name"] == "Living"
    assert data["category_group_slug"] == "living"
    assert data["spent"] == "75.00"
    assert data["remaining"] == "125.00"


def test_create_group_budget(client, test_user):
    living_group_id = _get_group_id(client, test_user, "living", "expense")

    response = client.post(
        "/api/v1/budgets",
        headers={"Authorization": f"Bearer {test_user}"},
        json={
            "name": "Living March",
            "amount": "400.00",
            "period_start": "2026-03-01",
            "period_end": "2026-03-31",
            "scope": "group",
            "category_group_id": living_group_id,
        },
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["scope"] == "group"
    assert data["status"] in {"active", "upcoming", "archived"}
    assert data["category_id"] is None
    assert data["category_name"] is None
    assert data["category_slug"] is None
    assert data["category_group_id"] == living_group_id
    assert data["category_group_name"] == "Living"
    assert data["category_group_slug"] == "living"


def test_budget_rejects_income_category(client, test_user):
    salary_category_id = _get_category_id(
        client,
        test_user,
        "salary",
        "income",
    )

    response = client.post(
        "/api/v1/budgets",
        headers={"Authorization": f"Bearer {test_user}"},
        json={
            "name": "Invalid",
            "amount": "200.00",
            "period_start": "2026-03-01",
            "period_end": "2026-03-31",
            "scope": "category",
            "category_id": salary_category_id,
        },
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_update_and_delete_budget(client, test_user):
    living_group_id = _get_group_id(client, test_user, "living", "expense")
    create_response = client.post(
        "/api/v1/budgets",
        headers={"Authorization": f"Bearer {test_user}"},
        json={
            "name": "Living March",
            "amount": "400.00",
            "period_start": "2026-03-01",
            "period_end": "2026-03-31",
            "scope": "group",
            "category_group_id": living_group_id,
        },
    )
    budget_id = create_response.json()["id"]

    update_response = client.put(
        f"/api/v1/budgets/{budget_id}",
        headers={"Authorization": f"Bearer {test_user}"},
        json={"amount": "450.00"},
    )
    assert update_response.status_code == status.HTTP_200_OK
    assert update_response.json()["amount"] == "450.00"

    delete_response = client.delete(
        f"/api/v1/budgets/{budget_id}",
        headers={"Authorization": f"Bearer {test_user}"},
    )
    assert delete_response.status_code == status.HTTP_204_NO_CONTENT


def test_budget_rejects_duplicate_target_same_period(client, test_user):
    groceries_category_id = _get_category_id(
        client,
        test_user,
        "groceries",
        "expense",
    )
    payload = {
        "name": "Groceries March",
        "amount": "200.00",
        "period_start": "2026-03-01",
        "period_end": "2026-03-31",
        "scope": "category",
        "category_id": groceries_category_id,
    }

    first_response = client.post(
        "/api/v1/budgets",
        headers={"Authorization": f"Bearer {test_user}"},
        json=payload,
    )
    assert first_response.status_code == status.HTTP_201_CREATED

    duplicate_response = client.post(
        "/api/v1/budgets",
        headers={"Authorization": f"Bearer {test_user}"},
        json=payload | {"name": "Transportations typo"},
    )
    assert duplicate_response.status_code == status.HTTP_409_CONFLICT


def test_list_budgets_can_filter_by_status(client, test_user):
    groceries_category_id = _get_category_id(
        client,
        test_user,
        "groceries",
        "expense",
    )
    today = date.today()
    current_start = today.replace(day=1)
    current_end = today.replace(day=28) + timedelta(days=4)
    current_end = current_end - timedelta(days=current_end.day)
    previous_end = current_start - timedelta(days=1)
    previous_start = previous_end.replace(day=1)
    next_month_start = current_end + timedelta(days=1)
    next_month_end = next_month_start.replace(day=28) + timedelta(days=4)
    next_month_end = next_month_end - timedelta(days=next_month_end.day)

    budgets = [
        {
            "name": "Archived Groceries",
            "amount": "120.00",
            "period_start": previous_start.isoformat(),
            "period_end": previous_end.isoformat(),
            "scope": "category",
            "category_id": groceries_category_id,
        },
        {
            "name": "Active Groceries",
            "amount": "150.00",
            "period_start": current_start.isoformat(),
            "period_end": current_end.isoformat(),
            "scope": "category",
            "category_id": groceries_category_id,
        },
        {
            "name": "Upcoming Groceries",
            "amount": "180.00",
            "period_start": next_month_start.isoformat(),
            "period_end": next_month_end.isoformat(),
            "scope": "category",
            "category_id": groceries_category_id,
        },
    ]
    for budget in budgets:
        response = client.post(
            "/api/v1/budgets",
            headers={"Authorization": f"Bearer {test_user}"},
            json=budget,
        )
        assert response.status_code == status.HTTP_201_CREATED

    active_response = client.get(
        "/api/v1/budgets",
        headers={"Authorization": f"Bearer {test_user}"},
        params={"status": "active"},
    )
    assert active_response.status_code == status.HTTP_200_OK
    assert [budget["name"] for budget in active_response.json()] == [
        "Active Groceries"
    ]

    archived_response = client.get(
        "/api/v1/budgets",
        headers={"Authorization": f"Bearer {test_user}"},
        params={"status": "archived"},
    )
    assert archived_response.status_code == status.HTTP_200_OK
    assert [budget["name"] for budget in archived_response.json()] == [
        "Archived Groceries"
    ]

    upcoming_response = client.get(
        "/api/v1/budgets",
        headers={"Authorization": f"Bearer {test_user}"},
        params={"status": "upcoming"},
    )
    assert upcoming_response.status_code == status.HTTP_200_OK
    assert [budget["name"] for budget in upcoming_response.json()] == [
        "Upcoming Groceries"
    ]


def test_clone_budget_allows_new_name_period_and_amount(client, test_user):
    transport_category_id = _get_category_id(
        client,
        test_user,
        "transport",
        "expense",
    )
    create_response = client.post(
        "/api/v1/budgets",
        headers={"Authorization": f"Bearer {test_user}"},
        json={
            "name": "Transportation March",
            "amount": "40.00",
            "period_start": "2026-03-01",
            "period_end": "2026-03-31",
            "scope": "category",
            "category_id": transport_category_id,
        },
    )
    assert create_response.status_code == status.HTTP_201_CREATED
    budget_id = create_response.json()["id"]

    clone_response = client.post(
        f"/api/v1/budgets/{budget_id}/clone",
        headers={"Authorization": f"Bearer {test_user}"},
        json={
            "name": "Transportation April",
            "amount": "70.00",
            "period_start": "2026-04-01",
            "period_end": "2026-04-30",
        },
    )
    assert clone_response.status_code == status.HTTP_201_CREATED
    cloned = clone_response.json()
    assert cloned["name"] == "Transportation April"
    assert cloned["amount"] == "70.00"
    assert cloned["category_id"] == transport_category_id
    assert cloned["period_start"] == "2026-04-01"
    assert cloned["period_end"] == "2026-04-30"
