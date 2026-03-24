import pytest  # type: ignore
from uuid import uuid4
from sqlmodel import Session, SQLModel, create_engine
from fastapi.testclient import TestClient
from src.main import app
from src.core.database import get_db  # type: ignore
from src.models import User


sqlite_url = "sqlite://"
engine = create_engine(
    sqlite_url,
    connect_args={"check_same_thread": False},
)


@pytest.fixture(name="session")
def session_fixture():
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    SQLModel.metadata.drop_all(engine)


@pytest.fixture(name="client")
def client_fixture(session: Session):
    def get_map_db():
        yield session

    app.dependency_overrides[get_db] = get_map_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(session: Session):
    """Factory fixture to create a valid user for testing."""
    user = User(
        id=uuid4(),
        username="test_marla",
        email="test@spendflow.app",
        hashed_password="hashed_placeholder",
        timezone="UTC",
        currency="USD",
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user
