"""Test configuration and shared fixtures."""

import asyncio
import os
import tempfile
from datetime import timedelta
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlmodel import SQLModel

from src.core.security import create_access_token
from src.database import get_session
from src.main import app
from src.models import User

# Create a temporary directory for test databases
test_db_dir = tempfile.gettempdir()


# Create unique test database per session
def get_test_db_path():
    """Generate a unique test database path."""
    import uuid

    db_name = f"test_{uuid.uuid4().hex[:8]}.db"
    return os.path.join(test_db_dir, db_name)


# Use file-based SQLite for better concurrency/isolation
sqlite_url_template = "sqlite+aiosqlite:///{db_path}"

# Will be set in fixture
_engine = None
_db_path = None


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """Set up test database engine at session scope."""
    global _engine, _db_path
    _db_path = get_test_db_path()
    _engine = create_async_engine(
        sqlite_url_template.format(db_path=_db_path),
        connect_args={"check_same_thread": False},
        echo=False,
    )
    yield
    # Cleanup
    if os.path.exists(_db_path):
        try:
            os.remove(_db_path)
        except OSError:
            pass


AsyncSessionLocal = None


def _get_session_local():
    """Get or create AsyncSessionLocal."""
    global AsyncSessionLocal, _engine
    if AsyncSessionLocal is None:
        AsyncSessionLocal = async_sessionmaker(
            _engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
    return AsyncSessionLocal


@pytest.fixture(scope="function")
def event_loop():
    """Create an event loop for the test."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()


@pytest.fixture
def session(event_loop):
    """Create a fresh async test database session for each test."""

    async def init():
        async_session_local = _get_session_local()
        # Create all tables
        async with _engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)

        # Create fresh session
        new_session = async_session_local()
        return new_session

    session = event_loop.run_until_complete(init())
    yield session

    # Cleanup
    async def cleanup():
        await session.close()
        # Clear all data for next test
        async with _engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.drop_all)

    event_loop.run_until_complete(cleanup())


@pytest.fixture
def client(session):
    """Create a test client with overridden database session."""

    # Override with an async generator for proper async dependency injection
    async def get_session_override():
        yield session

    app.dependency_overrides[get_session] = get_session_override
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def test_user_object(session, event_loop):
    """Create a test user and return the user object."""

    async def create_user():
        user = User(
            id=uuid4(),
            username="test_user",
            email="test@example.com",
            hashed_password=(
                "$2b$12$abcdefghijklmnopqrstupppphashed_password_placeholder"
            ),
            timezone="UTC",
            currency="USD",
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user

    user = event_loop.run_until_complete(create_user())
    return user


@pytest.fixture
def test_user(test_user_object):
    """Create JWT token for test user (uses same user as test_user_object)."""
    token = create_access_token(
        subject=str(test_user_object.id),
        expires_delta=timedelta(hours=24),
    )
    return token
