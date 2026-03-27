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
- **Database**: Stores users, accounts, budgets, recurring rules, and ledger transactions.
- **Log Aggregator**: Receives structured logs for monitoring.
- **User**: Authenticates and interacts with the system.

---

## Key Features
- **User Authentication**: JWT-based, secure password hashing, registration, and login endpoints.
- **Account Management**: Create, list, soft-delete, and restore accounts. Opening balances are recorded as ledger entries and balances remain derivable from transactions.
- **Recurring Rules & Projections**: Define recurring income/expenses, including every N days/weeks/months/years via an interval. Project future transactions for any period, with weekend adjustment rules.
- **Security**: Rate limiting, CORS, security headers, and centralized error handling.
- **Extensible**: Modular codebase, easy to add new endpoints or business logic.

---

## API Endpoints (v1)

### Authentication
- `POST /api/v1/auth/register` — Register a new user
- `POST /api/v1/auth/login` — Obtain JWT token

### Accounts
- `POST /api/v1/accounts` — Create an account with an optional opening balance ledger entry
- `GET /api/v1/accounts` — List all active accounts
- `GET /api/v1/accounts/{account_id}` — Get a single account
- `PUT /api/v1/accounts/{account_id}` — Update account name or type
- `DELETE /api/v1/accounts/{account_id}` — Soft-delete an account
- `POST /api/v1/accounts/{account_id}/restore` — Restore a soft-deleted account

### Calendar/Projections
- `GET /api/v1/calendar/projection?account_id=...&month=...&year=...` — Get projected recurring transactions with running projected balance for a given account and month
- `POST /api/v1/calendar/rules` — Create a recurring rule
- `GET /api/v1/calendar/rules` — List recurring rules, optionally filtered by `account_id`
- `GET /api/v1/calendar/rules/{rule_id}` — Get a recurring rule
- `PUT /api/v1/calendar/rules/{rule_id}` — Update a recurring rule
- `DELETE /api/v1/calendar/rules/{rule_id}` — Soft-delete a recurring rule

### Transactions
- `POST /api/v1/transactions` — Create a regular income or expense ledger entry
- `POST /api/v1/transactions/adjustments` — Create a manual adjustment ledger entry
- `POST /api/v1/transactions/transfers` — Move money atomically between two accounts
- `GET /api/v1/transactions` — List transactions with optional filters such as `type`, `account_id`, `category_id`, `date_from`, and `date_to`

### Budgets
- `POST /api/v1/budgets` — Create a budget for one expense category or category group
- `GET /api/v1/budgets` — List budgets with computed spent, remaining amount, lifecycle status, and optional filters such as `status`, `year`, `month`, `period_start_from`, and `period_end_to`
- `GET /api/v1/budgets/{budget_id}` — Get one budget
- `PUT /api/v1/budgets/{budget_id}` — Update a budget target or date range
- `POST /api/v1/budgets/{budget_id}/clone` — Create a new budget from an existing one while changing name, amount, and period
- `DELETE /api/v1/budgets/{budget_id}` — Delete a budget

---

## Data Model

- **User**: username, email, hashed_password, timezone, currency, default_weekend_adjustment, created_at, updated_at
- **Account**: id, name, account_type, balance, user_id, deleted_at
- **Transaction**: id, description, amount, type, kind, account_id, category_id, transfer_group_id, transaction_date
- **Budget**: id, name, amount, period_start, period_end, scope, status, category_id or category_group_id
- **RecurringRule**: id, description, amount, type, frequency, interval, start_date, end_date, weekend_adjustment, account_id

---

## Example: Projected Transactions

The `/calendar/projection` endpoint returns a list of projected transactions for a given account and month, applying weekend adjustment rules (e.g., move to Friday or Monday if a transaction falls on a weekend).

---

## How to Use (for Frontend)

1. **Register/Login**: Obtain a JWT token via `/auth/register` and `/auth/login`.
2. **Authenticate**: Pass the JWT token as a Bearer token in the `Authorization` header for all requests.
3. **Accounts**: Use `/api/v1/accounts` endpoints to manage user accounts.
4. **Recurring Rules**: Use `/calendar/rules` to create weekly, monthly, or interval-based rules such as every 15 days.
5. **Budgets**: Use `/api/v1/budgets` to track planned versus actual expense spending, filter by lifecycle (`active`, `upcoming`, `archived`), and clone budgets from a previous period.
6. **Projections**: Use `/calendar/projection` to fetch virtual/projected transactions with projected balances for cash flow checks.

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
