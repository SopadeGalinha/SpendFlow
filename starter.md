# SpendFlow Starter Guide

This guide starts from a clean Docker reset and shows how to:

1. Register a user
2. Log in
3. Create one or more accounts
4. Add recurring income and recurring expenses
5. Add one-off income and expense transactions
6. Check projected balance in 20 days, even when you have multiple accounts

## 1. Start the app

From the project root, start the stack:

```bash
docker compose up --build -d
```

The API will be available at:

```bash
http://localhost:8000
```

Optional checks:

```bash
curl http://localhost:8000/health
curl http://localhost:8000/
```

Swagger UI is available at:

```text
http://localhost:8000/docs
```

## 2. Set a few shell variables

These make the examples easier to reuse:

```bash
export BASE_URL="http://localhost:8000"
export TODAY="$(date -I)"
export TARGET_DATE="$(date -I -d '+20 days')"
```

## 3. Register a user

Use `POST /api/v1/auth/register`.

```bash
curl -X POST "$BASE_URL/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "maria",
    "email": "maria@example.com",
    "password": "StrongPass123",
    "timezone": "Europe/Lisbon",
    "currency": "EUR"
  }'
```

Expected result:

```json
{
  "id": "...",
  "username": "maria",
  "email": "maria@example.com",
  "timezone": "Europe/Lisbon",
  "currency": "EUR",
  "created_at": "...",
  "updated_at": "..."
}
```

## 4. Log in and save the token

Login uses form data, not JSON.

Important detail: the `username` form field must contain the email.

```bash
export TOKEN=$(curl -s -X POST "$BASE_URL/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=maria@example.com&password=StrongPass123" | jq -r '.access_token')

echo "$TOKEN"
```

If `jq` is not installed, install it first or read the token manually from the JSON response.

## 5. Create accounts

The accounts route is:

```text
POST /api/v1/accounts/accounts
```

Create a main checking account:

```bash
export CHECKING_ID=$(curl -s -X POST "$BASE_URL/api/v1/accounts/accounts" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Main Checking",
    "balance": "2500.00"
  }' | jq -r '.id')

echo "$CHECKING_ID"
```

Create a savings account:

```bash
export SAVINGS_ID=$(curl -s -X POST "$BASE_URL/api/v1/accounts/accounts" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Savings",
    "balance": "5000.00"
  }' | jq -r '.id')

echo "$SAVINGS_ID"
```

List all accounts:

```bash
curl -s "$BASE_URL/api/v1/accounts/accounts" \
  -H "Authorization: Bearer $TOKEN" | jq
```

## 6. List available categories

Transactions support categories. The app ships with default categories.

List income categories:

```bash
curl -s "$BASE_URL/api/v1/categories?type=income" \
  -H "Authorization: Bearer $TOKEN" | jq
```

List expense categories:

```bash
curl -s "$BASE_URL/api/v1/categories?type=expense" \
  -H "Authorization: Bearer $TOKEN" | jq
```

You can save category IDs if you want to assign them in transactions.

Example:

```bash
export SALARY_CATEGORY_ID=$(curl -s "$BASE_URL/api/v1/categories?type=income" \
  -H "Authorization: Bearer $TOKEN" | jq -r '.[] | select(.slug == "salary") | .id')

export GROCERIES_CATEGORY_ID=$(curl -s "$BASE_URL/api/v1/categories?type=expense" \
  -H "Authorization: Bearer $TOKEN" | jq -r '.[] | select(.slug == "groceries") | .id')

export HOUSING_CATEGORY_ID=$(curl -s "$BASE_URL/api/v1/categories?type=expense" \
  -H "Authorization: Bearer $TOKEN" | jq -r '.[] | select(.slug == "housing") | .id')
```

## 7. Add recurring income

Recurring rules use:

```text
POST /api/v1/calendar/rules
```

All amounts must be positive.

Monthly salary on the 1st:

```bash
curl -X POST "$BASE_URL/api/v1/calendar/rules" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Monthly Salary",
    "amount": "3200.00",
    "type": "income",
    "frequency": "monthly",
    "interval": 1,
    "start_date": "2026-04-01",
    "weekend_adjustment": "following",
    "account_id": "'"$CHECKING_ID"'"
  }'
```

## 8. Add recurring expenses

### Example A: Monthly rent

```bash
curl -X POST "$BASE_URL/api/v1/calendar/rules" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Rent",
    "amount": "950.00",
    "type": "expense",
    "frequency": "monthly",
    "interval": 1,
    "start_date": "2026-04-05",
    "weekend_adjustment": "preceding",
    "account_id": "'"$CHECKING_ID"'"
  }'
```

### Example B: Gym every 15 days

This is the `every N days` case:

```bash
curl -X POST "$BASE_URL/api/v1/calendar/rules" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Gym",
    "amount": "25.00",
    "type": "expense",
    "frequency": "daily",
    "interval": 15,
    "start_date": "2026-04-01",
    "weekend_adjustment": "keep",
    "account_id": "'"$CHECKING_ID"'"
  }'
```

### Example C: Savings transfer-like income into another account

If you also want recurring deposits into savings, create the rule on the savings account:

```bash
curl -X POST "$BASE_URL/api/v1/calendar/rules" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Monthly Savings Deposit",
    "amount": "300.00",
    "type": "income",
    "frequency": "monthly",
    "interval": 1,
    "start_date": "2026-04-10",
    "weekend_adjustment": "keep",
    "account_id": "'"$SAVINGS_ID"'"
  }'
```

List recurring rules:

```bash
curl -s "$BASE_URL/api/v1/calendar/rules" \
  -H "Authorization: Bearer $TOKEN" | jq
```

## 9. Add one-off transactions

Use:

```text
POST /api/v1/transactions
```

Important rules:

1. `amount` must be positive
2. Use `type: income` or `type: expense` to decide the balance effect
3. Expenses reduce balance automatically
4. Incomes increase balance automatically

### One-off income example

```bash
curl -X POST "$BASE_URL/api/v1/transactions" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Freelance Payment",
    "amount": "450.00",
    "type": "income",
    "transaction_date": "'"$TODAY"'",
    "account_id": "'"$CHECKING_ID"'",
    "category_id": "'"$SALARY_CATEGORY_ID"'"
  }'
```

### One-off expense example

```bash
curl -X POST "$BASE_URL/api/v1/transactions" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Groceries",
    "amount": "85.30",
    "type": "expense",
    "transaction_date": "'"$TODAY"'",
    "account_id": "'"$CHECKING_ID"'",
    "category_id": "'"$GROCERIES_CATEGORY_ID"'"
  }'
```

List transactions:

```bash
curl -s "$BASE_URL/api/v1/transactions" \
  -H "Authorization: Bearer $TOKEN" | jq
```

## 10. Check the calendar for one account

The calendar projection endpoint is account-specific:

```text
GET /api/v1/calendar/projection?account_id=...&month=...&year=...
```

To see the projection for checking account in the target month:

```bash
export TARGET_MONTH=$(date +%-m -d "$TARGET_DATE")
export TARGET_YEAR=$(date +%Y -d "$TARGET_DATE")

curl -s "$BASE_URL/api/v1/calendar/projection?account_id=$CHECKING_ID&month=$TARGET_MONTH&year=$TARGET_YEAR" \
  -H "Authorization: Bearer $TOKEN" | jq
```

Each projection item includes:

1. `amount`
2. `balance_delta`
3. `projected_balance`
4. `date`

`projected_balance` is per account, not global across all accounts.

## 11. Check your balance in 20 days with multiple accounts

This is the important part.

Because projections are account-specific, the correct way to answer:

```text
What will my balance be in 20 days?
```

is:

1. List all accounts and read each current balance
2. For each account, fetch calendar projections for the months that intersect the range from today to target date
3. Sum each account's `balance_delta` for projection items with `date` between today and target date
4. Add that delta to the account's current balance
5. Sum all account projected balances if you want a portfolio-wide total

### Copy-paste script for all accounts

This script prints projected balance per account and a global total for `today + 20 days`.

```bash
BASE_URL="http://localhost:8000"
TODAY="$(date -I)"
TARGET_DATE="$(date -I -d '+20 days')"

CURRENT_MONTH=$(date +%-m -d "$TODAY")
CURRENT_YEAR=$(date +%Y -d "$TODAY")
TARGET_MONTH=$(date +%-m -d "$TARGET_DATE")
TARGET_YEAR=$(date +%Y -d "$TARGET_DATE")

accounts_json=$(curl -s "$BASE_URL/api/v1/accounts/accounts" \
  -H "Authorization: Bearer $TOKEN")

total="0"

for row in $(echo "$accounts_json" | jq -r '.[] | @base64'); do
  _jq() {
    echo "$row" | base64 -d | jq -r "$1"
  }

  account_id=$(_jq '.id')
  account_name=$(_jq '.name')
  current_balance=$(_jq '.balance')

  month_one=$(curl -s "$BASE_URL/api/v1/calendar/projection?account_id=$account_id&month=$CURRENT_MONTH&year=$CURRENT_YEAR" \
    -H "Authorization: Bearer $TOKEN")

  if [ "$CURRENT_MONTH" = "$TARGET_MONTH" ] && [ "$CURRENT_YEAR" = "$TARGET_YEAR" ]; then
    combined="$month_one"
  else
    month_two=$(curl -s "$BASE_URL/api/v1/calendar/projection?account_id=$account_id&month=$TARGET_MONTH&year=$TARGET_YEAR" \
      -H "Authorization: Bearer $TOKEN")
    combined=$(jq -s 'add' <(echo "$month_one") <(echo "$month_two"))
  fi

  delta=$(echo "$combined" | jq -r \
    --arg today "$TODAY" \
    --arg target "$TARGET_DATE" \
    '[.[] | select(.date >= $today and .date <= $target) | (.balance_delta | tonumber)] | add // 0')

  projected=$(awk "BEGIN { printf \"%.2f\", $current_balance + $delta }")
  total=$(awk "BEGIN { printf \"%.2f\", $total + $projected }")

  echo "$account_name | current=$current_balance | delta_until_$TARGET_DATE=$delta | projected=$projected"
done

echo "TOTAL_PROJECTED_BALANCE_ON_$TARGET_DATE=$total"
```

### Why this works

1. Accounts are separate balance buckets
2. The calendar endpoint projects one account at a time
3. `balance_delta` lets you add only the future recurring movements that happen before the target date
4. Summing per-account projected balances gives you the global future balance across all accounts

## 12. Useful follow-up calls

Get a single account:

```bash
curl -s "$BASE_URL/api/v1/accounts/accounts/$CHECKING_ID" \
  -H "Authorization: Bearer $TOKEN" | jq
```

Filter transactions by type:

```bash
curl -s "$BASE_URL/api/v1/transactions?type=expense" \
  -H "Authorization: Bearer $TOKEN" | jq
```

Filter transactions by account:

```bash
curl -s "$BASE_URL/api/v1/transactions?account_id=$CHECKING_ID" \
  -H "Authorization: Bearer $TOKEN" | jq
```

## 13. Rules to remember

1. Login expects form data, not JSON
2. Login uses email in the `username` field
3. Transaction amounts must always be positive
4. Recurring-rule amounts must always be positive
5. Use `type` to decide whether money goes in or out
6. Calendar projection is account-specific
7. To know your total future balance across multiple accounts, sum the per-account projections