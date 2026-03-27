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
- `POST /api/v1/transactions/incomes` — Deprecated compatibility alias for legacy clients
- `POST /api/v1/transactions/expenses` — Deprecated compatibility alias for legacy clients

### Budgets
- `POST /api/v1/budgets` — Create a budget for one expense category or category group
- `GET /api/v1/budgets` — List budgets with computed spent and remaining amounts
- `GET /api/v1/budgets/{budget_id}` — Get one budget
- `PUT /api/v1/budgets/{budget_id}` — Update a budget target or date range
- `DELETE /api/v1/budgets/{budget_id}` — Delete a budget

---

## Data Model

- **User**: username, email, hashed_password, timezone, currency, default_weekend_adjustment, created_at, updated_at
- **Account**: id, name, account_type, balance, user_id, deleted_at
- **Transaction**: id, description, amount, type, kind, account_id, category_id, transfer_group_id, transaction_date
- **Budget**: id, name, amount, period_start, period_end, scope, category_id or category_group_id
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
5. **Budgets**: Use `/api/v1/budgets` to track planned versus actual expense spending.
6. **Projections**: Use `/calendar/projection` to fetch virtual/projected transactions with projected balances for cash flow checks.

---

## Guia Rápido de Uso via API

Fluxo pensado para usar a aplicação como um usuário comum, mas fazendo tudo por API.

### 1. Defina a URL base

```bash
export BASE_URL="http://localhost:8000"
```

### 2. Crie sua conta

```bash
curl -X POST "$BASE_URL/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "paulo",
    "email": "paulo@example.com",
    "password": "StrongPass123",
    "timezone": "America/Sao_Paulo",
    "currency": "BRL",
    "default_weekend_adjustment": "following"
  }'
```

### 3. Faça login e guarde o token

```bash
export TOKEN=$(curl -s -X POST "$BASE_URL/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=paulo&password=StrongPass123" | jq -r '.access_token')
```

Se não tiver `jq`, faça o login e copie manualmente o campo `access_token`.

### 4. Crie sua conta principal

Exemplo: uma conta corrente com saldo inicial.

```bash
export CHECKING_ID=$(curl -s -X POST "$BASE_URL/api/v1/accounts" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Conta Principal",
    "account_type": "checking",
    "opening_balance": "3500.00"
  }' | jq -r '.id')
```

### 5. Crie uma segunda conta para reserva

```bash
export SAVINGS_ID=$(curl -s -X POST "$BASE_URL/api/v1/accounts" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Reserva",
    "account_type": "savings",
    "opening_balance": "500.00"
  }' | jq -r '.id')
```

### 6. Liste as categorias disponíveis

As categorias padrão já existem. Você normalmente vai usar essas categorias para transações e budgets.

```bash
curl -X GET "$BASE_URL/api/v1/categories?type=expense" \
  -H "Authorization: Bearer $TOKEN"
```

```bash
curl -X GET "$BASE_URL/api/v1/categories/groups?type=expense" \
  -H "Authorization: Bearer $TOKEN"
```

Pegue os IDs que quiser usar. Exemplos comuns:
- categoria `groceries`
- categoria `salary`
- grupo `living`

### 7. Lance uma receita

Exemplo: salário entrando na conta principal.

```bash
export SALARY_CATEGORY_ID="coloque-aqui-o-id-da-categoria-salary"

curl -X POST "$BASE_URL/api/v1/transactions" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"description\": \"Salario de marco\",
    \"amount\": \"8000.00\",
    \"type\": \"income\",
    \"transaction_date\": \"2026-03-05\",
    \"account_id\": \"$CHECKING_ID\",
    \"category_id\": \"$SALARY_CATEGORY_ID\"
  }"
```

### 8. Lance uma despesa

Exemplo: supermercado.

```bash
export GROCERIES_CATEGORY_ID="coloque-aqui-o-id-da-categoria-groceries"

curl -X POST "$BASE_URL/api/v1/transactions" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"description\": \"Supermercado\",
    \"amount\": \"240.90\",
    \"type\": \"expense\",
    \"transaction_date\": \"2026-03-06\",
    \"account_id\": \"$CHECKING_ID\",
    \"category_id\": \"$GROCERIES_CATEGORY_ID\"
  }"
```

### 9. Transfira dinheiro entre contas

Exemplo: mandar dinheiro da conta principal para a reserva.

```bash
curl -X POST "$BASE_URL/api/v1/transactions/transfers" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"description\": \"Transferencia para reserva\",
    \"amount\": \"1000.00\",
    \"transaction_date\": \"2026-03-07\",
    \"from_account_id\": \"$CHECKING_ID\",
    \"to_account_id\": \"$SAVINGS_ID\"
  }"
```

### 10. Faça um ajuste manual se precisar reconciliar saldo

Use isso só quando precisar corrigir diferença real de saldo.

```bash
curl -X POST "$BASE_URL/api/v1/transactions/adjustments" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"description\": \"Ajuste de conciliacao\",
    \"amount\": \"15.00\",
    \"type\": \"expense\",
    \"transaction_date\": \"2026-03-08\",
    \"account_id\": \"$CHECKING_ID\"
  }"
```

### 11. Liste as transações

```bash
curl -X GET "$BASE_URL/api/v1/transactions?account_id=$CHECKING_ID" \
  -H "Authorization: Bearer $TOKEN"
```

### 12. Crie um budget por categoria

Exemplo: limitar supermercado no mês.

```bash
curl -X POST "$BASE_URL/api/v1/budgets" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"name\": \"Budget Mercado Marco\",
    \"amount\": \"1200.00\",
    \"period_start\": \"2026-03-01\",
    \"period_end\": \"2026-03-31\",
    \"scope\": \"category\",
    \"category_id\": \"$GROCERIES_CATEGORY_ID\"
  }"
```

### 13. Crie um budget por grupo

Exemplo: orçamento geral de despesas da casa.

```bash
export LIVING_GROUP_ID="coloque-aqui-o-id-do-grupo-living"

curl -X POST "$BASE_URL/api/v1/budgets" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"name\": \"Budget Casa Marco\",
    \"amount\": \"3000.00\",
    \"period_start\": \"2026-03-01\",
    \"period_end\": \"2026-03-31\",
    \"scope\": \"group\",
    \"category_group_id\": \"$LIVING_GROUP_ID\"
  }"
```

### 14. Consulte seus budgets com gasto e saldo restante

```bash
curl -X GET "$BASE_URL/api/v1/budgets" \
  -H "Authorization: Bearer $TOKEN"
```

O retorno já traz campos como:
- `spent`
- `remaining`

### 15. Consulte a projeção do calendário

Exemplo para ver o impacto das recorrências em uma conta específica.

```bash
curl -X GET "$BASE_URL/api/v1/calendar/projection?account_id=$CHECKING_ID&month=3&year=2026" \
  -H "Authorization: Bearer $TOKEN"
```

### Fluxo mínimo recomendado

Se quiser testar rápido sem pensar muito, a ordem prática é:

1. Registrar usuário.
2. Fazer login.
3. Criar uma conta `checking`.
4. Criar uma conta `savings`.
5. Buscar categorias padrão.
6. Inserir uma receita.
7. Inserir uma despesa.
8. Criar uma transferência.
9. Criar um budget.
10. Listar transações e budgets para conferir o resultado.

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
