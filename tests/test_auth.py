"""Tests for authentication endpoints."""

from fastapi import status


def test_register_valid_user(client):
    """Test successful user registration."""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "SecurePassword123",
            "timezone": "Europe/Lisbon",
            "currency": "EUR",
        },
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["username"] == "newuser"
    assert data["email"] == "newuser@example.com"
    assert "hashed_password" not in data
    assert data["timezone"] == "Europe/Lisbon"
    assert data["currency"] == "EUR"


def test_register_normalizes_username_and_email(client):
    """Username and email should be trimmed and lowercased."""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "  NewUser  ",
            "email": "  NewUser@Example.com  ",
            "password": "SecurePassword123",
            "timezone": "Europe/Lisbon",
            "currency": "EUR",
        },
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["username"] == "newuser"
    assert data["email"] == "newuser@example.com"


def test_register_duplicate_email(client, session, event_loop):
    """Test that registering with existing email fails."""
    from uuid import uuid4

    from src.core.security import get_password_hash
    from src.models import User

    async def setup():
        existing_user = User(
            id=uuid4(),
            username="existing",
            email="existing@example.com",
            hashed_password=get_password_hash("password123"),
            timezone="UTC",
            currency="USD",
        )
        session.add(existing_user)
        await session.commit()

    event_loop.run_until_complete(setup())

    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "different_user",
            "email": "existing@example.com",
            "password": "password123",
        },
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "already registered" in response.json()["detail"]


def test_register_duplicate_email_is_case_insensitive(
    client, session, event_loop
):
    """Email uniqueness should ignore case and outer whitespace."""
    from uuid import uuid4

    from src.core.security import get_password_hash
    from src.models import User

    async def setup():
        existing_user = User(
            id=uuid4(),
            username="existing",
            email="existing@example.com",
            hashed_password=get_password_hash("password123"),
            timezone="UTC",
            currency="USD",
        )
        session.add(existing_user)
        await session.commit()

    event_loop.run_until_complete(setup())

    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "different_user",
            "email": "  Existing@Example.com  ",
            "password": "password123",
        },
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "already registered" in response.json()["detail"]


def test_register_duplicate_username(client, session, event_loop):
    """Test that registering with existing username fails."""
    from uuid import uuid4

    from src.core.security import get_password_hash
    from src.models import User

    async def setup():
        existing_user = User(
            id=uuid4(),
            username="existing_user",
            email="different@example.com",
            hashed_password=get_password_hash("password123"),
            timezone="UTC",
            currency="USD",
        )
        session.add(existing_user)
        await session.commit()

    event_loop.run_until_complete(setup())

    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "existing_user",
            "email": "newemail@example.com",
            "password": "password123",
        },
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "already registered" in response.json()["detail"]


def test_register_duplicate_username_is_case_insensitive(
    client, session, event_loop
):
    """Username uniqueness should ignore case and outer whitespace."""
    from uuid import uuid4

    from src.core.security import get_password_hash
    from src.models import User

    async def setup():
        existing_user = User(
            id=uuid4(),
            username="existing_user",
            email="different@example.com",
            hashed_password=get_password_hash("password123"),
            timezone="UTC",
            currency="USD",
        )
        session.add(existing_user)
        await session.commit()

    event_loop.run_until_complete(setup())

    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "  Existing_User  ",
            "email": "newemail@example.com",
            "password": "password123",
        },
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "already registered" in response.json()["detail"]


def test_register_password_too_short(client):
    """Test that password with less than 8 characters fails."""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "Short1",
            "timezone": "UTC",
            "currency": "USD",
        },
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert "Short1" not in response.text
    assert response.json()["details"][0]["input"] == "***REDACTED***"


def test_register_password_too_long(client):
    """Test that password with more than 72 characters fails."""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "a" * 73,
            "timezone": "UTC",
            "currency": "USD",
        },
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_register_invalid_email(client):
    """Test that invalid email format fails."""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "newuser",
            "email": "invalid-email",
            "password": "SimplePassword123",
            "timezone": "UTC",
            "currency": "USD",
        },
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_register_missing_required_fields(client):
    """Test that missing required fields fail."""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "newuser",
        },
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_login_valid_credentials(client, session, event_loop):
    """Test successful login."""
    from uuid import uuid4

    from src.core.security import get_password_hash
    from src.models import User

    async def setup():
        user = User(
            id=uuid4(),
            username="loginuser",
            email="login@example.com",
            hashed_password=get_password_hash("password123"),
            timezone="UTC",
            currency="USD",
        )
        session.add(user)
        await session.commit()

    event_loop.run_until_complete(setup())

    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": "login@example.com",
            "password": "password123",
        },
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_email_is_case_insensitive_and_trimmed(
    client, session, event_loop
):
    """Login should normalize the email identifier."""
    from uuid import uuid4

    from src.core.security import get_password_hash
    from src.models import User

    async def setup():
        user = User(
            id=uuid4(),
            username="loginuser3",
            email="login3@example.com",
            hashed_password=get_password_hash("password123"),
            timezone="UTC",
            currency="USD",
        )
        session.add(user)
        await session.commit()

    event_loop.run_until_complete(setup())

    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": "  LOGIN3@EXAMPLE.COM  ",
            "password": "password123",
        },
    )
    assert response.status_code == status.HTTP_200_OK


def test_login_invalid_email(client):
    """Test login with non-existent email."""
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": "nonexistent@example.com",
            "password": "password123",
        },
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_login_wrong_password(client, session, event_loop):
    """Test login with wrong password."""
    from uuid import uuid4

    from src.core.security import get_password_hash
    from src.models import User

    async def setup():
        user = User(
            id=uuid4(),
            username="loginuser2",
            email="login2@example.com",
            hashed_password=get_password_hash("correctpassword"),
            timezone="UTC",
            currency="USD",
        )
        session.add(user)
        await session.commit()

    event_loop.run_until_complete(setup())

    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": "login2@example.com",
            "password": "wrongpassword",
        },
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_login_empty_password(client):
    """Test login with empty password."""
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": "user@example.com",
            "password": "",
        },
    )
    assert response.status_code in [
        status.HTTP_422_UNPROCESSABLE_CONTENT,
        status.HTTP_401_UNAUTHORIZED,
    ]
