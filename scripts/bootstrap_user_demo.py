#!/usr/bin/env python3

import argparse
import json
import sys
from calendar import monthrange
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any
from urllib import error, parse, request

DEFAULT_BASE_URL = "http://localhost:8000"


@dataclass
class ApiClient:
    base_url: str
    token: str

    def _build_url(
        self,
        path: str,
        query: dict[str, str] | None = None,
    ) -> str:
        url = f"{self.base_url.rstrip('/')}{path}"
        if query:
            url = f"{url}?{parse.urlencode(query)}"
        return url

    def request(
        self,
        method: str,
        path: str,
        payload: dict[str, Any] | None = None,
        query: dict[str, str] | None = None,
    ) -> Any:
        body = None
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/json",
        }
        if payload is not None:
            body = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"
        req = request.Request(
            self._build_url(path, query),
            data=body,
            headers=headers,
            method=method,
        )
        try:
            with request.urlopen(req) as response:
                raw = response.read().decode("utf-8")
                if not raw:
                    return None
                return json.loads(raw)
        except error.HTTPError as exc:
            raw = exc.read().decode("utf-8")
            detail = raw
            try:
                detail = json.loads(raw)
            except json.JSONDecodeError:
                pass
            raise RuntimeError(
                f"{method} {path} failed with {exc.code}: {detail}"
            ) from exc
        except error.URLError as exc:
            raise RuntimeError(
                f"Could not reach API at {self.base_url}: {exc.reason}"
            ) from exc

    def get(self, path: str, query: dict[str, str] | None = None) -> Any:
        return self.request("GET", path, query=query)

    def post(self, path: str, payload: dict[str, Any]) -> Any:
        return self.request("POST", path, payload=payload)


def month_bounds(today: date) -> tuple[date, date]:
    first_day = today.replace(day=1)
    last_day = today.replace(day=monthrange(today.year, today.month)[1])
    return first_day, last_day


def get_category_by_slug(
    categories: list[dict[str, Any]],
    slug: str,
) -> dict[str, Any]:
    for category in categories:
        if category["slug"] == slug:
            return category
    raise RuntimeError(f"Required category '{slug}' not found.")


def get_group_by_slug(
    groups: list[dict[str, Any]],
    slug: str,
) -> dict[str, Any]:
    for group in groups:
        if group["slug"] == slug:
            return group
    raise RuntimeError(f"Required group '{slug}' not found.")


def create_accounts(
    client: ApiClient,
) -> tuple[dict[str, Any], dict[str, Any]]:
    checking = client.post(
        "/api/v1/accounts",
        {
            "name": "Main Checking",
            "account_type": "checking",
            "opening_balance": "0.00",
        },
    )
    savings = client.post(
        "/api/v1/accounts",
        {
            "name": "Emergency Savings",
            "account_type": "savings",
            "opening_balance": "0.00",
        },
    )
    return checking, savings


def create_seed_transactions(
    client: ApiClient,
    checking_id: str,
    savings_id: str,
    salary_category_id: str,
    groceries_category_id: str,
    entertainment_category_id: str,
    subscriptions_category_id: str,
    transport_category_id: str,
    today: date,
) -> None:
    client.post(
        "/api/v1/transactions",
        {
            "description": "Salary",
            "amount": "3000.00",
            "type": "income",
            "transaction_date": today.isoformat(),
            "account_id": checking_id,
            "category_id": salary_category_id,
        },
    )
    client.post(
        "/api/v1/transactions/transfers",
        {
            "description": "Transfer to savings",
            "amount": "400.00",
            "transaction_date": today.isoformat(),
            "from_account_id": checking_id,
            "to_account_id": savings_id,
        },
    )

    expenses = [
        (
            "Weekly groceries",
            "82.50",
            groceries_category_id,
            today.isoformat(),
        ),
        (
            "Cinema night",
            "18.00",
            entertainment_category_id,
            (today + timedelta(days=1)).isoformat(),
        ),
        (
            "Streaming subscriptions",
            "14.99",
            subscriptions_category_id,
            (today + timedelta(days=2)).isoformat(),
        ),
        (
            "Metro top-up",
            "37.00",
            transport_category_id,
            (today + timedelta(days=3)).isoformat(),
        ),
    ]
    for description, amount, category_id, transaction_date in expenses:
        client.post(
            "/api/v1/transactions",
            {
                "description": description,
                "amount": amount,
                "type": "expense",
                "transaction_date": transaction_date,
                "account_id": checking_id,
                "category_id": category_id,
            },
        )


def create_recurring_rules(
    client: ApiClient,
    checking_id: str,
    salary_category_id: str,
    housing_category_id: str,
    utilities_category_id: str,
    subscriptions_category_id: str,
    transport_category_id: str,
    month_start: date,
) -> None:
    recurring_rules = [
        {
            "description": "Recurring salary",
            "amount": "3000.00",
            "type": "income",
            "frequency": "monthly",
            "interval": 1,
            "start_date": month_start.isoformat(),
            "end_date": None,
            "weekend_adjustment": "following",
            "account_id": checking_id,
            "category_id": salary_category_id,
        },
        {
            "description": "Rent",
            "amount": "950.00",
            "type": "expense",
            "frequency": "monthly",
            "interval": 1,
            "start_date": month_start.isoformat(),
            "end_date": None,
            "weekend_adjustment": "preceding",
            "account_id": checking_id,
            "category_id": housing_category_id,
        },
        {
            "description": "Electricity bill",
            "amount": "65.00",
            "type": "expense",
            "frequency": "monthly",
            "interval": 1,
            "start_date": (month_start + timedelta(days=4)).isoformat(),
            "end_date": None,
            "weekend_adjustment": "following",
            "account_id": checking_id,
            "category_id": utilities_category_id,
        },
        {
            "description": "Gym membership",
            "amount": "29.99",
            "type": "expense",
            "frequency": "monthly",
            "interval": 1,
            "start_date": (month_start + timedelta(days=7)).isoformat(),
            "end_date": None,
            "weekend_adjustment": "keep",
            "account_id": checking_id,
            "category_id": subscriptions_category_id,
        },
        {
            "description": "Transport pass",
            "amount": "100.00",
            "type": "expense",
            "frequency": "monthly",
            "interval": 1,
            "start_date": (month_start + timedelta(days=9)).isoformat(),
            "end_date": None,
            "weekend_adjustment": "following",
            "account_id": checking_id,
            "category_id": transport_category_id,
        },
    ]
    for rule in recurring_rules:
        client.post("/api/v1/calendar/rules", rule)


def create_budgets(
    client: ApiClient,
    groceries_category_id: str,
    entertainment_category_id: str,
    subscriptions_category_id: str,
    transport_category_id: str,
    housing_category_id: str,
    utilities_category_id: str,
    living_group_id: str,
    lifestyle_group_id: str,
    month_start: date,
    month_end: date,
) -> None:
    budgets = [
        {
            "name": "Groceries Budget",
            "amount": "250.00",
            "period_start": month_start.isoformat(),
            "period_end": month_end.isoformat(),
            "scope": "category",
            "category_id": groceries_category_id,
        },
        {
            "name": "Transportation Budget",
            "amount": "100.00",
            "period_start": month_start.isoformat(),
            "period_end": month_end.isoformat(),
            "scope": "category",
            "category_id": transport_category_id,
        },
        {
            "name": "Entertainment Budget",
            "amount": "80.00",
            "period_start": month_start.isoformat(),
            "period_end": month_end.isoformat(),
            "scope": "category",
            "category_id": entertainment_category_id,
        },
        {
            "name": "Subscriptions Budget",
            "amount": "60.00",
            "period_start": month_start.isoformat(),
            "period_end": month_end.isoformat(),
            "scope": "category",
            "category_id": subscriptions_category_id,
        },
        {
            "name": "Housing Budget",
            "amount": "1100.00",
            "period_start": month_start.isoformat(),
            "period_end": month_end.isoformat(),
            "scope": "category",
            "category_id": housing_category_id,
        },
        {
            "name": "Utilities Budget",
            "amount": "150.00",
            "period_start": month_start.isoformat(),
            "period_end": month_end.isoformat(),
            "scope": "category",
            "category_id": utilities_category_id,
        },
        {
            "name": "Living Group Budget",
            "amount": "500.00",
            "period_start": month_start.isoformat(),
            "period_end": month_end.isoformat(),
            "scope": "group",
            "category_group_id": living_group_id,
        },
        {
            "name": "Lifestyle Group Budget",
            "amount": "180.00",
            "period_start": month_start.isoformat(),
            "period_end": month_end.isoformat(),
            "scope": "group",
            "category_group_id": lifestyle_group_id,
        },
    ]
    for budget in budgets:
        client.post("/api/v1/budgets", budget)


def print_summary(
    checking: dict[str, Any],
    savings: dict[str, Any],
    budgets: list[dict[str, Any]],
) -> None:
    print("\nAccounts")
    print(
        f"- Checking: {checking['name']} ({checking['id']}) "
        f"balance={checking['balance']}"
    )
    print(
        f"- Savings: {savings['name']} ({savings['id']}) "
        f"balance={savings['balance']}"
    )

    print("\nBudget usage")
    for budget in budgets:
        print(
            "- "
            f"{budget['name']}: target {budget['amount']}, "
            f"used {budget['spent']}, remaining {budget['remaining']}"
        )


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Bootstrap a realistic SpendFlow user scenario "
            "using only a JWT token."
        )
    )
    parser.add_argument("token", help="Bearer token for an existing user")
    parser.add_argument(
        "--base-url",
        default=DEFAULT_BASE_URL,
        help="API base URL, default: http://localhost:8000",
    )
    args = parser.parse_args()

    client = ApiClient(base_url=args.base_url, token=args.token)
    today = date.today()
    month_start, month_end = month_bounds(today)

    try:
        income_categories = client.get(
            "/api/v1/categories",
            query={"type": "income"},
        )
        expense_categories = client.get(
            "/api/v1/categories",
            query={"type": "expense"},
        )
        expense_groups = client.get(
            "/api/v1/categories/groups",
            query={"type": "expense"},
        )

        salary_category = get_category_by_slug(income_categories, "salary")
        groceries_category = get_category_by_slug(
            expense_categories,
            "groceries",
        )
        transport_category = get_category_by_slug(
            expense_categories,
            "transport",
        )
        entertainment_category = get_category_by_slug(
            expense_categories,
            "entertainment",
        )
        subscriptions_category = get_category_by_slug(
            expense_categories,
            "subscriptions",
        )
        housing_category = get_category_by_slug(expense_categories, "housing")
        utilities_category = get_category_by_slug(
            expense_categories,
            "utilities",
        )

        living_group = get_group_by_slug(expense_groups, "living")
        lifestyle_group = get_group_by_slug(expense_groups, "lifestyle")

        checking, savings = create_accounts(client)

        create_seed_transactions(
            client,
            checking["id"],
            savings["id"],
            salary_category["id"],
            groceries_category["id"],
            entertainment_category["id"],
            subscriptions_category["id"],
            transport_category["id"],
            today,
        )
        create_recurring_rules(
            client,
            checking["id"],
            salary_category["id"],
            housing_category["id"],
            utilities_category["id"],
            subscriptions_category["id"],
            transport_category["id"],
            month_start,
        )
        create_budgets(
            client,
            groceries_category["id"],
            entertainment_category["id"],
            subscriptions_category["id"],
            transport_category["id"],
            housing_category["id"],
            utilities_category["id"],
            living_group["id"],
            lifestyle_group["id"],
            month_start,
            month_end,
        )

        accounts = client.get("/api/v1/accounts")
        budgets = client.get("/api/v1/budgets")
    except RuntimeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    latest_checking = next(
        account
        for account in accounts
        if account["id"] == checking["id"]
    )
    latest_savings = next(
        account
        for account in accounts
        if account["id"] == savings["id"]
    )

    print_summary(latest_checking, latest_savings, budgets)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
