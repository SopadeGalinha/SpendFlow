"""Tests for categories and category groups catalog."""

from fastapi import status


def test_default_category_catalog_contains_pets_group(client, test_user):
    """Default catalog should include pets for onboarding scenarios."""
    response = client.get(
        "/api/v1/categories/catalog",
        headers={"Authorization": f"Bearer {test_user}"},
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    pets_groups = [group for group in data if group["slug"] == "pets"]
    assert len(pets_groups) == 1
    assert pets_groups[0]["categories"][0]["slug"] == "pets"


def test_default_catalog_contains_transfer_group(client, test_user):
    """Transfer categories should exist and be excluded from budget math."""
    response = client.get(
        "/api/v1/categories",
        headers={"Authorization": f"Bearer {test_user}"},
        params={"type": "transfer"},
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert any(item["slug"] == "transfer" for item in data)
    assert any(item["slug"] == "credit_card_payment" for item in data)
    assert all(item["exclude_from_budget"] is True for item in data)


def test_create_custom_category_group(client, test_user):
    """Users should be able to create custom groups."""
    response = client.post(
        "/api/v1/categories/groups",
        headers={"Authorization": f"Bearer {test_user}"},
        json={"name": "Kids", "type": "expense"},
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["slug"] == "kids"
    assert data["is_system"] is False


def test_create_custom_category_in_custom_group(client, test_user):
    """Users should be able to create categories in custom groups."""
    group_response = client.post(
        "/api/v1/categories/groups",
        headers={"Authorization": f"Bearer {test_user}"},
        json={"name": "Kids", "type": "expense"},
    )
    group_id = group_response.json()["id"]

    response = client.post(
        "/api/v1/categories",
        headers={"Authorization": f"Bearer {test_user}"},
        json={
            "name": "School Supplies",
            "type": "expense",
            "group_id": group_id,
        },
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["slug"] == "school_supplies"
    assert data["is_system"] is False


def test_custom_categories_are_user_scoped(
    client,
    test_user,
    session,
    event_loop,
):
    """User-created groups must not be visible to another user."""
    first_response = client.post(
        "/api/v1/categories/groups",
        headers={"Authorization": f"Bearer {test_user}"},
        json={"name": "Side Hustle", "type": "income"},
    )
    assert first_response.status_code == status.HTTP_201_CREATED

    from uuid import uuid4

    from src.core.security import create_access_token
    from src.models import User

    async def setup_other_user():
        other_user = User(
            id=uuid4(),
            username="categories_user",
            email="categories_user@example.com",
            hashed_password="placeholder",
            timezone="UTC",
            currency="USD",
        )
        session.add(other_user)
        await session.commit()
        return other_user

    other_user = event_loop.run_until_complete(setup_other_user())
    other_token = create_access_token(str(other_user.id))

    response = client.get(
        "/api/v1/categories/groups",
        headers={"Authorization": f"Bearer {other_token}"},
        params={"type": "income"},
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert all(group["slug"] != "side_hustle" for group in data)


def test_category_type_must_match_group_type(client, test_user):
    """Categories cannot be created under a mismatched group type."""
    groups_response = client.get(
        "/api/v1/categories/groups",
        headers={"Authorization": f"Bearer {test_user}"},
        params={"type": "income"},
    )
    income_group_id = groups_response.json()[0]["id"]

    response = client.post(
        "/api/v1/categories",
        headers={"Authorization": f"Bearer {test_user}"},
        json={
            "name": "Vet Bills",
            "type": "expense",
            "group_id": income_group_id,
        },
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
