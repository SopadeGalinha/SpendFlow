# SpendFlow API

![SpendFlow Architecture](docs/ARCHITECTURE.md)

## Overview
SpendFlow is a modern, secure, and extensible financial management API designed for SaaS and personal finance applications. It provides robust user authentication, account management, recurring transaction projections, and soft-deletion for safe data handling. The backend is built with FastAPI, SQLModel, and async SQLAlchemy, following best practices for security, maintainability, and scalability.

---

## System Architecture

```markdown
graph TD
    A[Frontend (Web/App)] -- REST/JSON --> B[SpendFlow API (FastAPI)]
    B -- SQLAlchemy/SQLModel --> C[(Database)]
    B -- Alembic --> C
    B -- Logging/Monitoring --> D[Log Aggregator]
    B -- Auth/JWT --> E[User]
```

- **Frontend**: Consumes REST endpoints, handles user interaction.
- **SpendFlow API**: Handles business logic, authentication, projections, and data integrity.
- **Database**: Stores users, accounts, recurring rules, and transactions.
- **Log Aggregator**: Receives structured logs for monitoring.
- **User**: Authenticates and interacts with the system.

---

## Key Features
- **User Authentication**: JWT-based, secure password hashing, registration, and login endpoints.
- **Account Management**: Create, list, soft-delete, and restore accounts. Soft-deleted accounts are hidden but recoverable.
- **Recurring Rules & Projections**: Define recurring income/expenses. Project future transactions for any period, with weekend adjustment rules.
- **Security**: Rate limiting, CORS, security headers, and centralized error handling.
- **Extensible**: Modular codebase, easy to add new endpoints or business logic.

---

## API Endpoints (v1)

### Authentication
- `POST /api/v1/auth/register` — Register a new user
- `POST /api/v1/auth/login` — Obtain JWT token

### Accounts
- `GET /api/v1/finance/accounts` — List all active accounts
- `DELETE /api/v1/finance/accounts/{account_id}` — Soft-delete an account
- `POST /api/v1/finance/accounts/{account_id}/restore` — Restore a soft-deleted account

### Calendar/Projections
- `GET /api/v1/calendar/projection?account_id=...&month=...&year=...` — Get projected transactions for a given account and month

---

## Data Model

- **User**: username, email, hashed_password, timezone, currency, default_weekend_adjustment, created_at, updated_at
- **Account**: id, name, balance, user_id, deleted_at
- **RecurringRule**: id, description, amount, type (income/expense), frequency, start_date, end_date, weekend_adjustment, account_id

---

## Example: Projected Transactions

The `/calendar/projection` endpoint returns a list of projected transactions for a given account and month, applying weekend adjustment rules (e.g., move to Friday or Monday if a transaction falls on a weekend).

---

## How to Use (for Frontend)

1. **Register/Login**: Obtain a JWT token via `/auth/register` and `/auth/login`.
2. **Authenticate**: Pass the JWT token as a Bearer token in the `Authorization` header for all requests.
3. **Accounts**: Use `/finance/accounts` endpoints to manage user accounts.
4. **Projections**: Use `/calendar/projection` to fetch virtual/projected transactions for display in calendars, dashboards, or cash flow charts.

---

## Error Handling
All errors are returned as JSON with clear messages and HTTP status codes. Example:
```json
{
  "error": "Validation Error",
  "message": "Invalid input data. Please check your request and try again.",
  "details": [...],
  "path": "/api/v1/finance/accounts"
}
```

---

## Security Notes
- All endpoints require authentication except `/auth/register` and `/auth/login`.
- Rate limiting and security headers are enforced.
- Never share your JWT token.

---

## Development & Contribution
- Backend: Python 3.11+, FastAPI, SQLModel, Alembic, async SQLAlchemy
- See `docs/` for architecture and migration details.
- Run tests with `pytest`.

---

## Contact
For questions or issues, contact the backend team or open an issue in the repository.
