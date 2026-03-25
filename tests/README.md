# Testing Guide

## Overview

This directory contains comprehensive test suites for the SpendFlow API. The tests are organized by functionality and cover:

- Authentication (registration and login)
- Account management (CRUD operations, soft delete, restore)
- Calendar projections
- Schema validation
- Business logic services
- Edge cases and security
- General API health checks

## Running Tests

### Prerequisites

Ensure you are in the project root directory and all dependencies are installed:

```bash
cd /path/to/spendlyFlow
poetry install
```

### Run All Tests

```bash
poetry run pytest tests/ -v
```

Or with explicit PYTHONPATH:

```bash
PYTHONPATH=/path/to/spendlyFlow poetry run pytest tests/ -v
```

### Run Specific Test File

```bash
poetry run pytest tests/test_auth.py -v
poetry run pytest tests/test_finance.py -v
poetry run pytest tests/test_schemas.py -v
```

### Run Specific Test

```bash
poetry run pytest tests/test_auth.py::test_login_valid_credentials -v
```

### Run with Coverage

```bash
poetry run pytest tests/ --cov=src --cov-report=html
```

The coverage report will be generated in `htmlcov/index.html`.

## Test Structure

### conftest.py

Contains shared fixtures used across all tests:

- `session`: Fresh SQLite test database for each test
- `client`: FastAPI TestClient with test database
- `test_user`: JWT token for authenticated requests
- `test_user_object`: User database object for reference

### test_auth.py

Tests for authentication endpoints:

- User registration with valid/invalid data
- Duplicate email/username detection
- Password validation (length, format)
- Login with valid/invalid credentials
- Wrong password handling
- Token generation

**Tests**: 10+

### test_api.py

General API tests:

- Health check endpoint
- Root endpoint
- Protected endpoints without token
- Invalid token handling
- Response headers

**Tests**: 5+

### test_finance.py

Account management tests:

- Create account
- List accounts
- Get single account
- Update account (name and balance)
- Soft delete account
- Restore deleted account
- Access control (other user's accounts)
- Validation (name, balance)

**Tests**: 10+

### test_calendar.py

Calendar projection tests:

- Empty projections
- Monthly recurring rules
- Multiple recurring rules
- Date range validation
- Authorization checks
- Deleted account handling
- Invalid parameters

**Tests**: 8+

### test_schemas.py

Schema validation tests:

- UserCreate schema validation
- AccountCreate/Update schemas
- ProjectionResponse serialization
- Password validation
- Email validation
- Decimal handling
- JSON serialization

**Tests**: 15+

### test_services.py

Business logic service tests:

- CalendarService date adjustment (weekday/weekend)
- Projection generation
- Password hashing and verification
- JWT token creation
- Authentication logic

**Tests**: 12+

### test_edge_cases.py

Edge cases and security tests:

- Cross-user access prevention
- Negative balance validation
- Deleted account access
- Special characters in names
- Large decimal values
- Multiple account creation
- Security headers
- CORS configuration

**Tests**: 10+

## Test Coverage

Current test coverage includes:

- **Authentication**: 100%
- **Accounts**: ~95%
- **Calendar Projections**: ~90%
- **Schemas**: ~85%
- **Services**: ~80%
- **General API**: ~90%

## Key Features

### Fixtures

Tests use pytest fixtures for:

- Database setup and teardown
- Test user creation
- JWT token generation
- Test client initialization

### Isolation

Each test:

- Gets a fresh database
- Is independent of other tests
- Cleans up after itself
- Can run in any order

### Async Support

The test suite supports async operations via `pytest-asyncio`.

## Common Patterns

### Testing Protected Endpoints

```python
def test_example(client, test_user):
    response = client.get(
        "/api/v1/accounts/accounts",
        headers={"Authorization": f"Bearer {test_user}"},
    )
    assert response.status_code == 200
```

### Testing with Database Objects

```python
def test_example(client, test_user, test_user_object, session):
    account = Account(
        name="Test",
        balance=Decimal("100.00"),
        user_id=test_user_object.id,
    )
    session.add(account)
    session.commit()
```

### Testing Validation

```python
def test_example(client):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "test",
            "email": "invalid-email",
            "password": "short",
        },
    )
    assert response.status_code == 422
```

## Debugging Tests

### Verbose Output

```bash
poetry run pytest tests/ -vv
```

### Print Debug Info

```bash
poetry run pytest tests/ -s
```

### Run with Logging

```bash
poetry run pytest tests/ --log-cli-level=DEBUG
```

### Specific Test with Debugging

```bash
poetry run pytest tests/test_auth.py::test_login_valid_credentials -vv -s
```

## CI/CD Integration

These tests are designed for CI/CD pipelines:

- Exit code 0 on success
- Exit code 1 on failure
- JSON report generation (for CI tools)

Example command for CI:

```bash
poetry run pytest tests/ --tb=short --json-report --json-report-file=report.json
```

## Adding New Tests

When adding new tests:

1. Create test file following pattern: `test_<feature>.py`
2. Use descriptive test names starting with `test_`
3. Add docstrings explaining what is tested
4. Use appropriate fixtures from `conftest.py`
5. Group related tests in test classes
6. Maintain test isolation

Example:

```python
def test_new_feature_success(client, test_user):
    """Test successful new feature behavior."""
    response = client.post(
        "/api/v1/endpoint",
        headers={"Authorization": f"Bearer {test_user}"},
        json={"key": "value"},
    )
    assert response.status_code == 201
```

## Known Limitations

- Tests use SQLite, not PostgreSQL (sufficient for development)
- Async database tests are limited (sync testing used instead)
- Rate limiting middleware is not tested (in-memory only)

## Troubleshooting

### ImportError: No module named 'src'

If you get an error like `ModuleNotFoundError: No module named 'src'`, ensure:

1. **You're in the project root directory**:
   ```bash
   cd /path/to/spendlyFlow
   ```

2. **Run tests with Poetry** (recommended):
   ```bash
   poetry run pytest tests/ -v
   ```

3. **Or set PYTHONPATH explicitly**:
   ```bash
   PYTHONPATH=/path/to/spendlyFlow poetry run pytest tests/ -v
   ```

### AsyncSession errors

If tests fail with async-related errors:

1. Ensure `aiosqlite` is installed:
   ```bash
   poetry install
   ```

2. Check that you're using `poetry run pytest` rather than running pytest directly

## Further Reading

- [pytest Documentation](https://docs.pytest.org/)
- [FastAPI Testing](https://fastapi.tiangolo.com/advanced/testing-dependencies/)
- [SQLModel Testing](https://sqlmodel.tiangolo.com/tutorial/create-db-and-table-session/)
