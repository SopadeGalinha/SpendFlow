# 📅 Virtual Calendar Engine

SpendlyFlow uses a **Virtual Projection** approach. We do not store thousands of future transaction rows; we calculate them on-the-fly based on **Recurring Rules**.

## 🧠 Business Logic: Weekend Adjustments

Financial transactions often cannot happen on weekends. We implemented three adjustment strategies:

| Strategy | Behavior |
| :--- | :--- |
| **KEEP** | No change. Transaction stays on Saturday/Sunday (Common for subscriptions like Netflix). |
| **FOLLOWING** | Moves the date to the next Monday (Common for Salaries). |
| **PRECEDING** | Moves the date to the previous Friday (Common for Rent or Bills). |

## ⚙️ How it works
1. The user requests a projection for a specific month/year.
2. The service fetches all `RecurringRules` for that user's accounts.
3. For each rule, it calculates the "theoretical" date.
4. If it's a weekend, it applies the rule's `weekend_adjustment`.
5. Returns a JSON list of "Virtual Transactions".

### 🚀 Performance Note
Projections are currently calculated in-memory for the requested range. For ranges larger than 24 months, we recommend implementing a cache layer or pagination to maintain the "Fast" in FastAPI.