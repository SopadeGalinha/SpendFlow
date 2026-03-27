"""Debug test to check authentication and user lookup."""

from datetime import timedelta
from uuid import uuid4

from fastapi import status

from src.core.security import create_access_token
from src.models import User


def test_debug_authenticated_request(client, session, event_loop):
    """Debug test to check if authenticated requests work."""

    # Create a test user
    async def create_test_user():
        test_user = User(
            id=uuid4(),
            username="debuguser",
            email="debug@example.com",
            hashed_password=(
                "$2b$12$abcdefghijklmnopqrstuppphashed_password_placeholder"
            ),
            timezone="UTC",
            currency="USD",
        )
        session.add(test_user)
        await session.commit()
        await session.refresh(test_user)
        return test_user

    user = event_loop.run_until_complete(create_test_user())
    print(f"Created user: {user.id}")

    # Create a JWT token for this user
    token = create_access_token(
        subject=str(user.id),
        expires_delta=timedelta(hours=24),
    )
    print(f"Created token: {token[:20]}...")

    # Try to call the protected endpoint
    response = client.get(
        "/api/v1/accounts",
        headers={"Authorization": f"Bearer {token}"},
    )

    print(f"Response status: {response.status_code}")
    if response.status_code != 200:
        print(f"Response body: {response.text}")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == []  # Should have no accounts
