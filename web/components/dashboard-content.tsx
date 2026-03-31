"use client";

import { useEffect, useRef, useState } from "react";

import {
  buildMonthSnapshots,
  synchronizeBudgetResponses,
  type AccountResponse,
  type BudgetResponse,
  type ProjectionResponse,
  type RecurringRuleResponse,
  type TransactionResponse,
} from "@/lib/mock-finance";

const WEEKDAY_LABELS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
const INITIAL_MONTH = new Date(new Date().getFullYear(), new Date().getMonth(), 1);
const MAX_VISIBLE_DAY_ITEMS = 2;
const USER_PREFERENCES_ENDPOINT = "/api/user-preferences";

type DashboardWidgetId =
  | "metrics"
  | "evolution"
  | "accounts_savings"
  | "budgets_recurring"
  | "calendar"
  | "transactions";

const DEFAULT_WIDGET_ORDER: DashboardWidgetId[] = [
  "metrics",
  "evolution",
  "accounts_savings",
  "budgets_recurring",
  "calendar",
  "transactions",
];

const WIDGET_LABELS: Record<DashboardWidgetId, string> = {
  metrics: "Top metrics",
  evolution: "Month evolution",
  accounts_savings: "Accounts and savings",
  budgets_recurring: "Budgets and recurring",
  calendar: "Recurring calendar",
  transactions: "Recent transactions",
};

type BillStatus = "paid" | "unpaid" | "overdue";
type BillTone = "housing" | "utilities" | "wellness" | "transport";

type CalendarBill = {
  id: string;
  projectionId: string;
  name: string;
  cadence: string;
  tone: BillTone;
  type: ProjectionResponse["type"];
  date: Date;
  monthKey: string;
  originalAmount: number;
  expectedAmount: number;
  paidAmount?: number;
  paidAt?: string;
  status: BillStatus;
  accountId: string;
  categoryId: string | null;
};

type CalendarDay = {
  key: string;
  date: Date;
  inMonth: boolean;
  isToday: boolean;
  bills: CalendarBill[];
};

const savingsGoal = {
  name: "Summer Escape",
  current: 1120,
  target: 2400,
  targetDate: "Jul 15, 2026",
};

function greetingForTime(date: Date) {
  const hour = date.getHours();
  if (hour < 12) {
    return "Good morning";
  }
  if (hour < 18) {
    return "Good afternoon";
  }
  return "Good evening";
}

function firstNameFromUsername(username: string) {
  const normalized = username.trim().split(/[._\s-]+/)[0];
  if (!normalized) {
    return "there";
  }

  return normalized.charAt(0).toUpperCase() + normalized.slice(1);
}

function shiftMonth(baseDate: Date, monthOffset: number) {
  return new Date(baseDate.getFullYear(), baseDate.getMonth() + monthOffset, 1);
}

function parseAmount(amount: string) {
  return Number(amount);
}

function formatCurrency(amount: number) {
  return `EUR ${amount.toLocaleString("en-US", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}`;
}

function sameDay(left: Date, right: Date) {
  return (
    left.getFullYear() === right.getFullYear() &&
    left.getMonth() === right.getMonth() &&
    left.getDate() === right.getDate()
  );
}

function formatMonthKey(date: Date) {
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}`;
}

function formatDayKey(date: Date) {
  return `${formatMonthKey(date)}-${String(date.getDate()).padStart(2, "0")}`;
}

function formatReadableDate(date: Date) {
  return date.toLocaleDateString("en-US", {
    weekday: "long",
    month: "long",
    day: "numeric",
  });
}

function formatAccountType(accountType: AccountResponse["account_type"]) {
  return accountType === "checking" ? "Daily cash account" : "Savings bucket";
}

function formatRelativeMonth(monthKey: string) {
  const [year, month] = monthKey.split("-").map(Number);
  return new Date(year, month - 1, 1).toLocaleDateString("en-US", {
    month: "long",
    year: "numeric",
  });
}

function getBillTone(ruleId: string): BillTone {
  if (ruleId === "rr-rent" || ruleId === "rr-coworking") {
    return "housing";
  }
  if (ruleId === "rr-transport-pass") {
    return "transport";
  }
  if (ruleId === "rr-therapy" || ruleId === "rr-gym") {
    return "wellness";
  }
  return "utilities";
}

function getRuleCategoryId(ruleId: string) {
  if (ruleId === "rr-rent" || ruleId === "rr-coworking") {
    return "91dd2d70-ae62-4760-bf52-b28665d90005";
  }
  if (ruleId === "rr-electricity") {
    return "91dd2d70-ae62-4760-bf52-b28665d90006";
  }
  if (ruleId === "rr-therapy") {
    return "91dd2d70-ae62-4760-bf52-b28665d90007";
  }
  if (ruleId === "rr-transport-pass") {
    return "91dd2d70-ae62-4760-bf52-b28665d90002";
  }
  return "91dd2d70-ae62-4760-bf52-b28665d90003";
}

function buildCalendarBills(
  monthKey: string,
  projections: ProjectionResponse[],
  recurringRules: RecurringRuleResponse[],
  transactions: TransactionResponse[],
) {
  const today = new Date();
  today.setHours(0, 0, 0, 0);

  return projections
    .filter((projection) => projection.date.startsWith(monthKey))
    .reduce<CalendarBill[]>((accumulator, projection) => {
      const rule = recurringRules.find((item) => item.id === projection.rule_id);
      if (!rule) {
        return accumulator;
      }

      const matchingTransaction = transactions.find(
        (transaction) =>
          transaction.description === projection.description &&
          transaction.account_id === rule.account_id &&
          transaction.type === projection.type &&
          transaction.transaction_date === projection.date,
      );
      const expectedAmount = parseAmount(projection.amount);
      const projectedDate = new Date(`${projection.date}T00:00:00`);
      const status: BillStatus = matchingTransaction
        ? "paid"
        : projectedDate < today
          ? "overdue"
          : "unpaid";

      accumulator.push({
        id: `${monthKey}-${projection.rule_id}`,
        projectionId: projection.id,
        name: projection.description,
        cadence: "Monthly",
        tone: getBillTone(projection.rule_id),
        type: projection.type,
        date: projectedDate,
        monthKey,
        originalAmount: parseAmount(rule.amount),
        expectedAmount,
        paidAmount: matchingTransaction ? parseAmount(matchingTransaction.amount) : undefined,
        paidAt: matchingTransaction?.transaction_date,
        status,
        accountId: rule.account_id,
        categoryId: getRuleCategoryId(rule.id),
      });

      return accumulator;
    }, [])
    .sort((left, right) => left.date.getTime() - right.date.getTime());
}

function buildCalendarDays(activeMonth: Date, monthBills: CalendarBill[]) {
  const firstDayOfMonth = new Date(
    activeMonth.getFullYear(),
    activeMonth.getMonth(),
    1,
  );
  const monthOffset = (firstDayOfMonth.getDay() + 6) % 7;
  const gridStart = new Date(
    activeMonth.getFullYear(),
    activeMonth.getMonth(),
    1 - monthOffset,
  );
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const billsByDay = monthBills.reduce<Record<string, CalendarBill[]>>(
    (accumulator, bill) => {
      const key = formatDayKey(bill.date);
      accumulator[key] = [...(accumulator[key] ?? []), bill];
      return accumulator;
    },
    {},
  );

  return Array.from({ length: 42 }, (_, index) => {
    const date = new Date(
      gridStart.getFullYear(),
      gridStart.getMonth(),
      gridStart.getDate() + index,
    );

    return {
      key: formatDayKey(date),
      date,
      inMonth: date.getMonth() === activeMonth.getMonth(),
      isToday: sameDay(date, today),
      bills: billsByDay[formatDayKey(date)] ?? [],
    } satisfies CalendarDay;
  });
}

function SparkBars({ values }: { values: number[] }) {
  const maxValue = Math.max(...values.map((value) => Math.abs(value)), 1);
  return (
    <div
      className="sparkbars"
      aria-hidden="true"
      style={{ gridTemplateColumns: `repeat(${values.length}, minmax(0, 1fr))` }}
    >
      {values.map((value, index) => (
        <span
          key={`${value}-${index}`}
          style={{ height: `${Math.max((Math.abs(value) / maxValue) * 100, 20)}%` }}
        />
      ))}
    </div>
  );
}

function BudgetBar({ spent, limit }: { spent: number; limit: number }) {
  const progress = Math.min((spent / limit) * 100, 100);
  return (
    <div className="budget-bar">
      <div className="budget-bar-fill" style={{ width: `${progress}%` }} />
    </div>
  );
}

function activityAmount(transaction: TransactionResponse) {
  const amount = formatCurrency(parseAmount(transaction.amount));
  if (transaction.type === "income") {
    return `+${amount}`;
  }
  if (transaction.kind === "transfer") {
    return amount;
  }
  return `-${amount}`;
}

function normalizeWidgetOrder(candidate: unknown): DashboardWidgetId[] {
  if (!Array.isArray(candidate)) {
    return DEFAULT_WIDGET_ORDER;
  }

  const filtered = candidate.filter((item): item is DashboardWidgetId =>
    typeof item === "string" && DEFAULT_WIDGET_ORDER.includes(item as DashboardWidgetId),
  );

  const unique = Array.from(new Set(filtered));
  const missing = DEFAULT_WIDGET_ORDER.filter((item) => !unique.includes(item));
  return [...unique, ...missing];
}

function normalizeHiddenWidgets(candidate: unknown): Set<DashboardWidgetId> {
  if (!Array.isArray(candidate)) {
    return new Set<DashboardWidgetId>();
  }

  return new Set(
    candidate.filter(
      (item): item is DashboardWidgetId =>
        typeof item === "string" && DEFAULT_WIDGET_ORDER.includes(item as DashboardWidgetId),
    ),
  );
}

type DashboardContentProps = {
  initialDataset: {
    accounts: AccountResponse[];
    transactions: TransactionResponse[];
    budgets: BudgetResponse[];
    recurringRules: RecurringRuleResponse[];
    projections: ProjectionResponse[];
  };
  greetingName?: string;
};

export function DashboardContent({ initialDataset, greetingName }: DashboardContentProps) {
  const modalRef = useRef<HTMLElement | null>(null);
  const [calendarMonth, setCalendarMonth] = useState(INITIAL_MONTH);
  const [accountsState, setAccountsState] = useState(initialDataset.accounts);
  const [transactionsState, setTransactionsState] = useState(initialDataset.transactions);
  const [selectedDayKey, setSelectedDayKey] = useState<string | null>(null);
  const [payingBillId, setPayingBillId] = useState<string | null>(null);
  const [paymentAmount, setPaymentAmount] = useState("");
  const [widgetOrder, setWidgetOrder] = useState<DashboardWidgetId[]>(
    DEFAULT_WIDGET_ORDER,
  );
  const [hiddenWidgets, setHiddenWidgets] = useState<Set<DashboardWidgetId>>(
    new Set<DashboardWidgetId>(),
  );
  const [preferencesReady, setPreferencesReady] = useState(false);

  const monthKey = formatMonthKey(calendarMonth);
  const syncedBudgets = synchronizeBudgetResponses(initialDataset.budgets, transactionsState);
  const monthBills = buildCalendarBills(
    monthKey,
    initialDataset.projections,
    initialDataset.recurringRules,
    transactionsState,
  );
  const calendarDays = buildCalendarDays(calendarMonth, monthBills);
  const selectedDay = calendarDays.find((day) => day.key === selectedDayKey) ?? null;
  const currentBudgets = syncedBudgets.filter((budget) => budget.period_start.startsWith(monthKey));
  const monthSnapshots = buildMonthSnapshots(
    transactionsState,
    syncedBudgets,
    initialDataset.projections,
    monthKey,
  );
  const currentSnapshot = monthSnapshots[monthSnapshots.length - 1];
  const totalBalance = accountsState.reduce(
    (sum, account) => sum + parseAmount(account.balance),
    0,
  );
  const savedPercentage = Math.round((savingsGoal.current / savingsGoal.target) * 100);
  const scheduledMonthTotal = monthBills.reduce(
    (sum, bill) => sum + bill.expectedAmount,
    0,
  );
  const overdueBills = monthBills.filter((bill) => bill.status === "overdue");
  const overdueTotal = overdueBills.reduce(
    (sum, bill) => sum + bill.expectedAmount,
    0,
  );
  const paidBills = monthBills.filter((bill) => bill.status === "paid");
  const paidTotal = paidBills.reduce(
    (sum, bill) => sum + (bill.paidAmount ?? bill.expectedAmount),
    0,
  );
  const unpaidTotal = monthBills
    .filter((bill) => bill.status !== "paid")
    .reduce((sum, bill) => sum + bill.expectedAmount, 0);
  const checkingBalance = parseAmount(
    accountsState.find((account) => account.account_type === "checking")?.balance ?? "0",
  );
  const spendableToday = checkingBalance - unpaidTotal;
  const onTrackBudgets = currentBudgets.filter(
    (budget) => parseAmount(budget.remaining) >= 0,
  );
  const recentTransactions = [...transactionsState]
    .sort((left, right) => {
      const dateCompare = right.transaction_date.localeCompare(left.transaction_date);
      if (dateCompare !== 0) {
        return dateCompare;
      }
      return right.updated_at.localeCompare(left.updated_at);
    })
    .slice(0, 8);
  const calendarLabel = formatRelativeMonth(monthKey);
  const nextRecurring = monthBills.find((bill) => bill.status !== "paid");
  const accountNames = Object.fromEntries(
    accountsState.map((account) => [account.id, account.name]),
  );
  const greeting = `${greetingForTime(new Date())}, ${firstNameFromUsername(greetingName ?? "")}.`;
  const heroCopy = overdueBills.length > 0
    ? `${overdueBills.length} recurring items still need confirmation, while ${onTrackBudgets.length} of ${currentBudgets.length} budgets remain inside guardrails.`
    : `Recurring payments are current and ${onTrackBudgets.length} of ${currentBudgets.length} budgets are still on track.`;

  useEffect(() => {
    let cancelled = false;

    async function loadPreferences() {
      try {
        const response = await fetch(USER_PREFERENCES_ENDPOINT, {
          method: "GET",
          cache: "no-store",
        });

        if (!response.ok) {
          return;
        }

        const payload = (await response.json()) as {
          dashboard?: {
            order?: unknown;
            hidden?: unknown;
          };
        };

        if (cancelled) {
          return;
        }

        setWidgetOrder(normalizeWidgetOrder(payload.dashboard?.order));
        setHiddenWidgets(normalizeHiddenWidgets(payload.dashboard?.hidden));
      } catch {
        return;
      } finally {
        if (!cancelled) {
          setPreferencesReady(true);
        }
      }
    }

    loadPreferences();

    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (!preferencesReady) {
      return;
    }

    const controller = new AbortController();
    const timeoutId = window.setTimeout(async () => {
      try {
        await fetch(USER_PREFERENCES_ENDPOINT, {
          method: "PUT",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            dashboard: {
              order: widgetOrder,
              hidden: Array.from(hiddenWidgets),
            },
          }),
          signal: controller.signal,
        });
      } catch {
        return;
      }
    }, 300);

    return () => {
      controller.abort();
      window.clearTimeout(timeoutId);
    };
  }, [hiddenWidgets, preferencesReady, widgetOrder]);

  useEffect(() => {
    if (!selectedDay) {
      document.body.style.overflow = "";
      return;
    }

    const modalElement = modalRef.current;
    const previousOverflow = document.body.style.overflow;
    const previousActiveElement = document.activeElement as HTMLElement | null;
    document.body.style.overflow = "hidden";

    const focusableElements = modalElement?.querySelectorAll<HTMLElement>(
      'button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), a[href], [tabindex]:not([tabindex="-1"])',
    );
    focusableElements?.[0]?.focus();

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        setSelectedDayKey(null);
        setPayingBillId(null);
        setPaymentAmount("");
        return;
      }

      if (event.key !== "Tab" || !modalElement) {
        return;
      }

      const currentFocusable = Array.from(
        modalElement.querySelectorAll<HTMLElement>(
          'button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), a[href], [tabindex]:not([tabindex="-1"])',
        ),
      );

      if (currentFocusable.length === 0) {
        return;
      }

      const firstElement = currentFocusable[0];
      const lastElement = currentFocusable[currentFocusable.length - 1];
      const activeElement = document.activeElement as HTMLElement | null;

      if (event.shiftKey && activeElement === firstElement) {
        event.preventDefault();
        lastElement.focus();
      } else if (!event.shiftKey && activeElement === lastElement) {
        event.preventDefault();
        firstElement.focus();
      }
    }

    window.addEventListener("keydown", handleKeyDown);

    return () => {
      document.body.style.overflow = previousOverflow;
      window.removeEventListener("keydown", handleKeyDown);
      previousActiveElement?.focus();
    };
  }, [selectedDay]);

  function openDay(dayKey: string) {
    setSelectedDayKey(dayKey);
    setPayingBillId(null);
    setPaymentAmount("");
  }

  function beginPayment(bill: CalendarBill) {
    setPayingBillId(bill.id);
    setPaymentAmount(bill.expectedAmount.toFixed(2));
  }

  function confirmPayment(bill: CalendarBill) {
    const numericAmount = Number(paymentAmount);
    if (!Number.isFinite(numericAmount) || numericAmount <= 0) {
      return;
    }

    const isoTimestamp = new Date().toISOString();
    const generatedTransaction: TransactionResponse = {
      id: `tx-local-${Date.now()}`,
      description: bill.name,
      amount: numericAmount.toFixed(2),
      type: bill.type,
      kind: "regular",
      transaction_date: bill.date.toISOString().slice(0, 10),
      account_id: bill.accountId,
      transfer_group_id: null,
      category_id: bill.categoryId,
      created_at: isoTimestamp,
      updated_at: isoTimestamp,
    };

    setTransactionsState((current) => [generatedTransaction, ...current]);
    setAccountsState((current) =>
      current.map((account) => {
        if (account.id !== bill.accountId) {
          return account;
        }

        const delta = bill.type === "expense" ? -numericAmount : numericAmount;
        return {
          ...account,
          balance: (parseAmount(account.balance) + delta).toFixed(2),
        } satisfies AccountResponse;
      }),
    );
    setPayingBillId(null);
    setPaymentAmount("");
  }

  function widgetOrderValue(widgetId: DashboardWidgetId) {
    const index = widgetOrder.indexOf(widgetId);
    return index < 0 ? DEFAULT_WIDGET_ORDER.indexOf(widgetId) : index;
  }

  function isWidgetVisible(widgetId: DashboardWidgetId) {
    return !hiddenWidgets.has(widgetId);
  }

  function toggleWidgetVisibility(widgetId: DashboardWidgetId, visible: boolean) {
    setHiddenWidgets((current) => {
      const next = new Set(current);
      if (visible) {
        next.delete(widgetId);
      } else {
        next.add(widgetId);
      }
      return next;
    });
  }

  function moveWidget(widgetId: DashboardWidgetId, direction: -1 | 1) {
    setWidgetOrder((current) => {
      const index = current.indexOf(widgetId);
      if (index < 0) {
        return current;
      }

      const nextIndex = index + direction;
      if (nextIndex < 0 || nextIndex >= current.length) {
        return current;
      }

      const next = [...current];
      const [item] = next.splice(index, 1);
      next.splice(nextIndex, 0, item);
      return next;
    });
  }

  return (
    <>
      <section className="hero-panel">
        <div>
          <p className="eyebrow">{calendarLabel} snapshot</p>
          <h2>{greeting}</h2>
          <p className="hero-copy">
            {heroCopy} {nextRecurring
              ? `Next action: ${nextRecurring.name} for ${formatCurrency(nextRecurring.expectedAmount)}.`
              : "Everything recurring is already confirmed for this month."}
          </p>
        </div>
        <div className="hero-stats">
          <div>
            <span>Total balance</span>
            <strong>{formatCurrency(totalBalance)}</strong>
          </div>
          <div>
            <span>Net this month</span>
            <strong>{formatCurrency(currentSnapshot?.net ?? 0)}</strong>
          </div>
          <SparkBars values={monthSnapshots.map((snapshot) => snapshot.net)} />
        </div>
      </section>

      <section className="panel dashboard-customizer">
        <div className="panel-heading">
          <div>
            <p className="eyebrow">Customize dashboard</p>
            <h3>Choose your focus widgets</h3>
          </div>
          <span className="pill">Saved on this device</span>
        </div>

        <div className="widget-config-list">
          {widgetOrder.map((widgetId, index) => (
            <div key={widgetId} className="widget-config-row">
              <label className="widget-toggle">
                <input
                  type="checkbox"
                  checked={isWidgetVisible(widgetId)}
                  onChange={(event) => {
                    toggleWidgetVisibility(widgetId, event.target.checked);
                  }}
                />
                <span>{WIDGET_LABELS[widgetId]}</span>
              </label>

              <div className="composer-inline-actions">
                <button
                  type="button"
                  className="day-tray-close"
                  onClick={() => moveWidget(widgetId, -1)}
                  disabled={index === 0}
                >
                  Move up
                </button>
                <button
                  type="button"
                  className="day-tray-close"
                  onClick={() => moveWidget(widgetId, 1)}
                  disabled={index === widgetOrder.length - 1}
                >
                  Move down
                </button>
              </div>
            </div>
          ))}
        </div>
      </section>

      <div className="dashboard-layout">

      {isWidgetVisible("metrics") ? (
      <section
        className="metrics-grid dashboard-widget"
        style={{ order: widgetOrderValue("metrics") }}
      >
        <article className="metric-card accent-sand">
          <p className="eyebrow">Spendable today</p>
          <strong>{formatCurrency(spendableToday)}</strong>
          <span>Checking balance after unpaid recurring items in {calendarLabel}.</span>
        </article>
        <article className="metric-card accent-foam">
          <p className="eyebrow">Budget health</p>
          <strong>
            {onTrackBudgets.length} of {currentBudgets.length} on track
          </strong>
          <span>
            {formatCurrency(currentSnapshot?.budget_spent ?? 0)} of {formatCurrency(currentSnapshot?.budgeted ?? 0)} planned budget has been used.
          </span>
        </article>
        <article className="metric-card accent-rose">
          <p className="eyebrow">Overdue recurring</p>
          <strong>{overdueBills.length} open bills</strong>
          <span>{formatCurrency(overdueTotal)} still not confirmed as paid.</span>
        </article>
      </section>
      ) : null}

      {isWidgetVisible("evolution") ? (
      <section
        className="panel wide-panel dashboard-widget"
        style={{ order: widgetOrderValue("evolution") }}
      >
        <div className="panel-heading">
          <div>
            <p className="eyebrow">Month evolution</p>
            <h3>Six months of cash flow context</h3>
          </div>
          <span className="pill">Authenticated history view</span>
        </div>
        <div className="evolution-grid">
          {monthSnapshots.map((snapshot) => {
            const savingsRate = snapshot.income > 0
              ? Math.round((snapshot.net / snapshot.income) * 100)
              : 0;
            const overBudget = snapshot.budget_spent - snapshot.budgeted;

            return (
              <article key={snapshot.month_key} className="evolution-card">
                <span className="eyebrow">{snapshot.label}</span>
                <strong>{formatCurrency(snapshot.net)}</strong>
                <p>
                  Income {formatCurrency(snapshot.income)} · Spend {formatCurrency(snapshot.expenses)}
                </p>
                <div className="evolution-meta">
                  <span>{savingsRate}% savings rate</span>
                  <span className={overBudget > 0 ? "trend-negative" : "trend-positive"}>
                    {overBudget > 0
                      ? `${formatCurrency(overBudget)} over budget`
                      : `${formatCurrency(Math.abs(overBudget))} under budget`}
                  </span>
                </div>
              </article>
            );
          })}
        </div>
      </section>
      ) : null}

      {isWidgetVisible("accounts_savings") ? (
      <section
        className="two-column dashboard-widget"
        style={{ order: widgetOrderValue("accounts_savings") }}
      >
        <article className="panel" id="accounts">
          <div className="panel-heading">
            <div>
              <p className="eyebrow">Accounts</p>
              <h3>Where the money sits</h3>
            </div>
            <a href="/accounts">See all</a>
          </div>
          <div className="account-list">
            {accountsState.map((account) => {
              const shareOfBalance = totalBalance > 0
                ? Math.round((parseAmount(account.balance) / totalBalance) * 100)
                : 0;

              return (
                <div key={account.id} className="account-row">
                  <div>
                    <strong>{account.name}</strong>
                    <span>{formatAccountType(account.account_type)}</span>
                  </div>
                  <div>
                    <strong>{formatCurrency(parseAmount(account.balance))}</strong>
                    <span>{shareOfBalance}% of total balances</span>
                  </div>
                </div>
              );
            })}
          </div>
        </article>

        <article className="panel" id="savings">
          <div className="panel-heading">
            <div>
              <p className="eyebrow">Savings</p>
              <h3>{savingsGoal.name}</h3>
            </div>
            <span className="pill">{savedPercentage}% funded</span>
          </div>
          <div className="goal-figure">EUR {savingsGoal.current.toLocaleString("en-US")}</div>
          <BudgetBar spent={savingsGoal.current} limit={savingsGoal.target} />
          <div className="goal-meta">
            <span>Target EUR {savingsGoal.target.toLocaleString("en-US")}</span>
            <span>{savingsGoal.targetDate}</span>
          </div>
        </article>
      </section>
      ) : null}

      {isWidgetVisible("budgets_recurring") ? (
      <section
        className="two-column dashboard-widget"
        style={{ order: widgetOrderValue("budgets_recurring") }}
      >
        <article className="panel" id="budget">
          <div className="panel-heading">
            <div>
              <p className="eyebrow">Budgets</p>
              <h3>Monthly guardrails</h3>
            </div>
            <a href="/budget">Manage</a>
          </div>
          <div className="budget-list">
            {currentBudgets.map((budget) => {
              const spent = parseAmount(budget.spent);
              const limit = parseAmount(budget.amount);
              const remaining = parseAmount(budget.remaining);
              const tone = remaining < 0 ? "alert" : remaining < limit * 0.2 ? "warning" : "calm";

              return (
                <div key={budget.id} className="budget-row">
                  <div className="budget-copy">
                    <strong>{budget.name}</strong>
                    <span>
                      Used {formatCurrency(spent)} · Remaining {formatCurrency(remaining)}
                    </span>
                  </div>
                  <div className={`budget-chip ${tone}`}>{formatCurrency(limit)}</div>
                  <BudgetBar spent={spent} limit={limit} />
                </div>
              );
            })}
          </div>
        </article>

        <article className="panel" id="recurring">
          <div className="panel-heading">
            <div>
              <p className="eyebrow">Recurring</p>
              <h3>Expected vs original</h3>
            </div>
            <a href="/calendar">Open calendar</a>
          </div>
          <div className="recurring-list">
            {monthBills.map((bill) => (
              <div key={bill.id} className="recurring-row">
                <div>
                  <strong>{bill.name}</strong>
                  <span>
                    {bill.cadence} · {bill.date.toLocaleDateString("en-US", {
                      month: "short",
                      day: "numeric",
                    })}
                  </span>
                </div>
                <div>
                  <strong>{formatCurrency(bill.expectedAmount)}</strong>
                  <span>Original {formatCurrency(bill.originalAmount)}</span>
                </div>
                <div className="recurring-row-meta">
                  <span className={`recurring-type ${bill.tone}`}>{bill.tone}</span>
                  <span className={`bill-status ${bill.status}`}>{bill.status}</span>
                </div>
              </div>
            ))}
          </div>
        </article>
      </section>
      ) : null}

      {isWidgetVisible("calendar") ? (
      <section
        className="panel wide-panel dashboard-widget"
        id="calendar"
        style={{ order: widgetOrderValue("calendar") }}
      >
        <div className="panel-heading calendar-heading">
          <div>
            <p className="eyebrow">Calendar</p>
            <h3>Recurring view</h3>
          </div>
          <div className="calendar-meta">
            <div className="calendar-summary">
              <span>Scheduled this month</span>
              <strong>{formatCurrency(scheduledMonthTotal)}</strong>
            </div>
            <div className="calendar-summary paid">
              <span>Paid</span>
              <strong>{formatCurrency(paidTotal)}</strong>
            </div>
            <div className="calendar-summary overdue">
              <span>Overdue</span>
              <strong>
                {overdueBills.length} · {formatCurrency(overdueTotal)}
              </strong>
            </div>
            <div className="calendar-toolbar" aria-label="Month controls">
              <button
                type="button"
                className="calendar-arrow"
                onClick={() => {
                  setCalendarMonth((current) => shiftMonth(current, -1));
                  setSelectedDayKey(null);
                  setPayingBillId(null);
                }}
                aria-label="Previous month"
              >
                &lt;
              </button>
              <strong className="calendar-month-label">{calendarLabel}</strong>
              <button
                type="button"
                className="calendar-arrow"
                onClick={() => {
                  setCalendarMonth((current) => shiftMonth(current, 1));
                  setSelectedDayKey(null);
                  setPayingBillId(null);
                }}
                aria-label="Next month"
              >
                &gt;
              </button>
            </div>
          </div>
        </div>

        <div className="calendar-scroll">
          <div
            className="calendar-grid"
            role="grid"
            aria-label={`Recurring calendar for ${calendarLabel}`}
          >
            {WEEKDAY_LABELS.map((label) => (
              <div key={label} className="calendar-weekday" role="columnheader">
                {label}
              </div>
            ))}

            {calendarDays.map((day) => {
              const previewBills = day.bills.slice(0, MAX_VISIBLE_DAY_ITEMS);
              const extraBills = day.bills.length - previewBills.length;
              const hasItems = day.bills.length > 0;
              const dayClassName = [
                "calendar-day",
                day.inMonth ? "" : "muted",
                day.isToday ? "today" : "",
                selectedDay?.key === day.key ? "selected" : "",
                day.bills.some((bill) => bill.status === "overdue") ? "has-overdue" : "",
                day.bills.every((bill) => bill.status === "paid") && hasItems ? "has-paid" : "",
                hasItems ? "interactive" : "",
              ]
                .filter(Boolean)
                .join(" ");

              if (hasItems) {
                return (
                  <button
                    key={day.key}
                    type="button"
                    className={dayClassName}
                    onClick={() => openDay(day.key)}
                  >
                    <div className="calendar-date">{day.date.getDate()}</div>
                    <div className="calendar-events">
                      {previewBills.map((bill) => (
                        <div
                          key={bill.id}
                          className={`calendar-event ${bill.tone} status-${bill.status}`}
                        >
                          <strong>{bill.name}</strong>
                          <span>{formatCurrency(bill.expectedAmount)}</span>
                        </div>
                      ))}
                      {extraBills > 0 ? (
                        <div className="calendar-overflow">+{extraBills} more bills</div>
                      ) : null}
                    </div>
                  </button>
                );
              }

              return (
                <div key={day.key} className={dayClassName} role="gridcell">
                  <div className="calendar-date">{day.date.getDate()}</div>
                </div>
              );
            })}
          </div>
        </div>
      </section>
      ) : null}

      {selectedDay && selectedDay.bills.length > 0 ? (
        <div
          className="day-modal-backdrop"
          role="presentation"
          onClick={() => {
            setSelectedDayKey(null);
            setPayingBillId(null);
          }}
        >
          <section
            className="day-modal"
            aria-label="Selected day details"
            role="dialog"
            aria-modal="true"
            ref={modalRef}
            tabIndex={-1}
            onClick={(event) => event.stopPropagation()}
          >
            <div className="day-tray-header">
              <div>
                <p className="eyebrow">Selected day</p>
                <h4>{formatReadableDate(selectedDay.date)}</h4>
              </div>
              <button
                type="button"
                className="day-tray-close"
                onClick={() => {
                  setSelectedDayKey(null);
                  setPayingBillId(null);
                }}
              >
                Close
              </button>
            </div>

            <div className="day-tray-list">
              {selectedDay.bills.map((bill) => (
                <article key={bill.id} className={`day-bill-card ${bill.status}`}>
                  <div className="day-bill-main">
                    <div>
                      <div className="day-bill-title-row">
                        <strong>{bill.name}</strong>
                        <span className={`recurring-type ${bill.tone}`}>{bill.tone}</span>
                        <span className={`bill-status ${bill.status}`}>{bill.status}</span>
                      </div>
                      <p>
                        Expected {formatCurrency(bill.expectedAmount)} · Original {formatCurrency(bill.originalAmount)}
                      </p>
                      {bill.status === "paid" ? (
                        <p>
                          Paid {formatCurrency(bill.paidAmount ?? bill.expectedAmount)} · Confirmed {bill.paidAt}
                        </p>
                      ) : (
                        <p>
                          {bill.status === "overdue"
                            ? "This bill is overdue and still missing a payment confirmation."
                            : "This bill is scheduled and waiting for confirmation."}
                        </p>
                      )}
                    </div>

                    {bill.status !== "paid" ? (
                      <button
                        type="button"
                        className="pay-button"
                        onClick={() => beginPayment(bill)}
                      >
                        Pay bill
                      </button>
                    ) : (
                      <span className="pay-complete">Transaction created</span>
                    )}
                  </div>

                  {payingBillId === bill.id ? (
                    <div className="pay-tray">
                      <label className="pay-field">
                        <span>Confirm payment amount</span>
                        <input
                          type="number"
                          min="0"
                          step="0.01"
                          value={paymentAmount}
                          onChange={(event) => setPaymentAmount(event.target.value)}
                        />
                      </label>
                      <div className="pay-actions">
                        <button
                          type="button"
                          className="pay-button confirm"
                          onClick={() => confirmPayment(bill)}
                        >
                          Confirm and create transaction
                        </button>
                        <button
                          type="button"
                          className="pay-button secondary"
                          onClick={() => {
                            setPayingBillId(null);
                            setPaymentAmount("");
                          }}
                        >
                          Cancel
                        </button>
                      </div>
                    </div>
                  ) : null}
                </article>
              ))}
            </div>
          </section>
        </div>
      ) : null}

      {isWidgetVisible("transactions") ? (
      <section
        className="panel wide-panel dashboard-widget"
        id="transactions"
        style={{ order: widgetOrderValue("transactions") }}
      >
        <div className="panel-heading">
          <div>
            <p className="eyebrow">Transactions</p>
            <h3>Recent movement</h3>
          </div>
          <a href="/transactions">Open ledger</a>
        </div>
        <div className="activity-list">
          {recentTransactions.map((transaction) => (
            <div key={transaction.id} className="activity-row">
              <div>
                <strong>{transaction.description}</strong>
                <span>
                  {new Date(`${transaction.transaction_date}T00:00:00`).toLocaleDateString("en-US", {
                    month: "short",
                    day: "numeric",
                  })} · {transaction.kind} · {accountNames[transaction.account_id] ?? "Linked account"}
                </span>
              </div>
              <span className={`amount ${transaction.type}`}>{activityAmount(transaction)}</span>
            </div>
          ))}
        </div>
      </section>
      ) : null}
      </div>
    </>
  );
}