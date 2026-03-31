"use client";

import { useActionState, useEffect, useMemo, useRef, useState } from "react";
import { useRouter } from "next/navigation";

import type { FinanceActionState } from "@/app/finance-actions";
import type { CategoryResponse } from "@/lib/finance-client";
import type { AccountResponse, BudgetResponse } from "@/lib/mock-finance";
import { emitShellToast } from "@/lib/ui-feedback";

const INITIAL_STATE: FinanceActionState = {
  error: null,
  ok: false,
  message: null,
  submittedAt: null,
};

const SLOW_SUBMIT_THRESHOLD_MS = 8000;

type FinanceFormAction = (
  state: FinanceActionState,
  formData: FormData,
) => Promise<FinanceActionState>;

type RecurringFrequency = "daily" | "weekly" | "monthly" | "yearly";

type WeekendAdjustment = "keep" | "following" | "preceding";

type RecurringPreviewItem = {
  isoDate: string;
  label: string;
};

type MutationFeedbackOptions = {
  state: FinanceActionState;
  isPending: boolean;
  successTitle: string;
  defaultSuccessDescription: string;
  onSuccess: () => void;
};

type CreateAccountFormProps = {
  action: FinanceFormAction;
};

type CreateTransactionFormProps = {
  action: FinanceFormAction;
  accounts: AccountResponse[];
  incomeCategories: CategoryResponse[];
  expenseCategories: CategoryResponse[];
};

type CreateBudgetFormProps = {
  action: FinanceFormAction;
  categories: CategoryResponse[];
  templates: BudgetResponse[];
};

type CreateRecurringRuleFormProps = {
  action: FinanceFormAction;
  accounts: AccountResponse[];
};

function todayIsoDate() {
  return new Date().toISOString().slice(0, 10);
}

function parseIsoLocalDate(value: string) {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(value)) {
    return null;
  }

  const [year, month, day] = value.split("-").map(Number);
  const parsed = new Date(year, month - 1, day);

  if (
    parsed.getFullYear() !== year ||
    parsed.getMonth() !== month - 1 ||
    parsed.getDate() !== day
  ) {
    return null;
  }

  return parsed;
}

function toIsoLocalDate(date: Date) {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function addMonthsPreservingDay(date: Date, monthsToAdd: number) {
  const year = date.getFullYear();
  const month = date.getMonth();
  const day = date.getDate();

  const anchor = new Date(year, month, 1);
  anchor.setMonth(anchor.getMonth() + monthsToAdd);

  const lastDay = new Date(
    anchor.getFullYear(),
    anchor.getMonth() + 1,
    0,
  ).getDate();

  return new Date(
    anchor.getFullYear(),
    anchor.getMonth(),
    Math.min(day, lastDay),
  );
}

function advanceRecurringDate(
  date: Date,
  frequency: RecurringFrequency,
  interval: number,
) {
  const next = new Date(date);

  if (frequency === "daily") {
    next.setDate(next.getDate() + interval);
    return next;
  }

  if (frequency === "weekly") {
    next.setDate(next.getDate() + interval * 7);
    return next;
  }

  if (frequency === "monthly") {
    return addMonthsPreservingDay(next, interval);
  }

  return addMonthsPreservingDay(next, interval * 12);
}

function applyWeekendAdjustment(
  date: Date,
  adjustment: WeekendAdjustment,
) {
  if (adjustment === "keep") {
    return new Date(date);
  }

  const adjusted = new Date(date);
  const day = adjusted.getDay();

  if (day !== 0 && day !== 6) {
    return adjusted;
  }

  if (adjustment === "following") {
    adjusted.setDate(adjusted.getDate() + (day === 6 ? 2 : 1));
    return adjusted;
  }

  adjusted.setDate(adjusted.getDate() - (day === 6 ? 1 : 2));
  return adjusted;
}

function buildRecurringPreviewDates(args: {
  startDate: string;
  endDate?: string;
  frequency: RecurringFrequency;
  intervalRaw: string;
  weekendAdjustment: WeekendAdjustment;
  count?: number;
}) {
  const count = args.count ?? 3;
  const start = parseIsoLocalDate(args.startDate);
  if (!start) {
    return [] as RecurringPreviewItem[];
  }

  const interval = Number(args.intervalRaw);
  if (!Number.isInteger(interval) || interval < 1) {
    return [] as RecurringPreviewItem[];
  }

  const end = args.endDate ? parseIsoLocalDate(args.endDate) : null;
  if (end && end < start) {
    return [] as RecurringPreviewItem[];
  }

  const preview: RecurringPreviewItem[] = [];
  let recurrenceDate = new Date(start);

  for (let index = 0; index < count; index += 1) {
    if (end && recurrenceDate > end) {
      break;
    }

    const adjustedDate = applyWeekendAdjustment(
      recurrenceDate,
      args.weekendAdjustment,
    );

    if (!end || adjustedDate <= end) {
      preview.push({
        isoDate: toIsoLocalDate(adjustedDate),
        label: adjustedDate.toLocaleDateString("en-US", {
          weekday: "short",
          month: "short",
          day: "numeric",
          year: "numeric",
        }),
      });
    }

    recurrenceDate = advanceRecurringDate(
      recurrenceDate,
      args.frequency,
      interval,
    );
  }

  return preview;
}

function useMutationFeedback({
  state,
  isPending,
  successTitle,
  defaultSuccessDescription,
  onSuccess,
}: MutationFeedbackOptions) {
  const router = useRouter();
  const [isSlow, setIsSlow] = useState(false);
  const lastSubmissionHandledRef = useRef<number | null>(null);
  const slowWarningToastShownRef = useRef(false);

  useEffect(() => {
    if (!isPending) {
      setIsSlow(false);
      slowWarningToastShownRef.current = false;
      return;
    }

    const timeoutId = window.setTimeout(() => {
      setIsSlow(true);

      if (slowWarningToastShownRef.current) {
        return;
      }

      slowWarningToastShownRef.current = true;
      emitShellToast({
        level: "warning",
        title: "Still saving",
        description:
          "This request is taking longer than expected. You can wait a bit more or reload the page.",
        durationMs: 7000,
      });
    }, SLOW_SUBMIT_THRESHOLD_MS);

    return () => {
      window.clearTimeout(timeoutId);
    };
  }, [isPending]);

  useEffect(() => {
    if (!state.submittedAt) {
      return;
    }

    if (lastSubmissionHandledRef.current === state.submittedAt) {
      return;
    }

    lastSubmissionHandledRef.current = state.submittedAt;

    if (state.ok) {
      onSuccess();
      router.refresh();
      emitShellToast({
        level: "success",
        title: successTitle,
        description: state.message ?? defaultSuccessDescription,
      });
      return;
    }

    if (state.error) {
      emitShellToast({
        level: "error",
        title: "Action failed",
        description: state.error,
        durationMs: 7000,
      });
    }
  }, [
    defaultSuccessDescription,
    onSuccess,
    router,
    state.error,
    state.message,
    state.ok,
    state.submittedAt,
    successTitle,
  ]);

  return {
    isSlow,
    recover: () => {
      window.location.reload();
    },
  };
}

function firstDayOfMonth() {
  const now = new Date();
  return new Date(now.getFullYear(), now.getMonth(), 1).toISOString().slice(0, 10);
}

function lastDayOfMonth() {
  const now = new Date();
  return new Date(now.getFullYear(), now.getMonth() + 1, 0).toISOString().slice(0, 10);
}

function shiftBudgetTemplatePeriod(periodStart: string, periodEnd: string) {
  const parsedStart = parseIsoLocalDate(periodStart);
  const parsedEnd = parseIsoLocalDate(periodEnd);

  if (!parsedStart || !parsedEnd) {
    return {
      periodStart: firstDayOfMonth(),
      periodEnd: lastDayOfMonth(),
    };
  }

  return {
    periodStart: toIsoLocalDate(addMonthsPreservingDay(parsedStart, 1)),
    periodEnd: toIsoLocalDate(addMonthsPreservingDay(parsedEnd, 1)),
  };
}

function formatBudgetTemplateOption(template: BudgetResponse) {
  const monthLabel = new Date(`${template.period_start}T00:00:00`).toLocaleDateString(
    "en-US",
    {
      month: "short",
      year: "numeric",
    },
  );

  return `${template.name} · EUR ${template.amount} · ${monthLabel}`;
}

export function CreateAccountForm({ action }: CreateAccountFormProps) {
  const [state, formAction, isPending] = useActionState(action, INITIAL_STATE);
  const formRef = useRef<HTMLFormElement>(null);

  const { isSlow, recover } = useMutationFeedback({
    state,
    isPending,
    successTitle: "Account saved",
    defaultSuccessDescription: "Your account is now available in balances.",
    onSuccess: () => {
      formRef.current?.reset();
    },
  });

  return (
    <section className="panel composer-panel">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">New account</p>
          <h3>Add checking or savings account</h3>
        </div>
      </div>

      <form ref={formRef} action={formAction} className="composer-form">
        <div className="composer-grid two-columns">
          <label className="composer-field">
            <span>Account name</span>
            <input
              name="name"
              type="text"
              placeholder="Main Checking"
              minLength={1}
              maxLength={255}
              required
            />
          </label>

          <label className="composer-field">
            <span>Account type</span>
            <select name="account_type" defaultValue="checking" required>
              <option value="checking">Checking</option>
              <option value="savings">Savings</option>
            </select>
          </label>

          <label className="composer-field">
            <span>Opening balance (optional)</span>
            <input
              name="opening_balance"
              type="number"
              placeholder="0.00"
              min="0"
              step="0.01"
            />
          </label>
        </div>

        {state.error ? <p className="composer-error">{state.error}</p> : null}

        {isSlow ? (
          <div className="composer-warning" role="status">
            <span>Still saving. This is taking longer than expected.</span>
            <button type="button" className="composer-recover" onClick={recover}>
              Reload page
            </button>
          </div>
        ) : null}

        <button type="submit" className="composer-submit" disabled={isPending}>
          {isPending ? "Saving..." : "Create account"}
        </button>
      </form>
    </section>
  );
}

export function CreateTransactionForm({
  action,
  accounts,
  incomeCategories,
  expenseCategories,
}: CreateTransactionFormProps) {
  const [state, formAction, isPending] = useActionState(action, INITIAL_STATE);
  const [transactionType, setTransactionType] = useState<"income" | "expense">("expense");
  const formRef = useRef<HTMLFormElement>(null);

  const { isSlow, recover } = useMutationFeedback({
    state,
    isPending,
    successTitle: "Transaction saved",
    defaultSuccessDescription: "Your ledger has been updated.",
    onSuccess: () => {
      formRef.current?.reset();
      setTransactionType("expense");
    },
  });

  const visibleCategories = useMemo(
    () => (transactionType === "income" ? incomeCategories : expenseCategories),
    [expenseCategories, incomeCategories, transactionType],
  );

  const isDisabled = accounts.length === 0 || isPending;

  return (
    <section className="panel composer-panel">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">New entry</p>
          <h3>Add income or expense</h3>
        </div>
      </div>

      {accounts.length === 0 ? (
        <p className="composer-help">Create an account first to post transactions.</p>
      ) : null}

      <form ref={formRef} action={formAction} className="composer-form">
        <fieldset className="composer-fieldset" disabled={isDisabled}>
          <div className="composer-grid three-columns">
            <label className="composer-field">
              <span>Type</span>
              <select
                name="type"
                value={transactionType}
                onChange={(event) => {
                  const nextType = event.target.value;
                  if (nextType === "income" || nextType === "expense") {
                    setTransactionType(nextType);
                  }
                }}
                required
              >
                <option value="expense">Expense</option>
                <option value="income">Income</option>
              </select>
            </label>

            <label className="composer-field">
              <span>Amount</span>
              <input
                name="amount"
                type="number"
                placeholder="0.00"
                min="0.01"
                step="0.01"
                required
              />
            </label>

            <label className="composer-field">
              <span>Date</span>
              <input
                name="transaction_date"
                type="date"
                defaultValue={todayIsoDate()}
                required
              />
            </label>

            <label className="composer-field full-width">
              <span>Description</span>
              <input
                name="description"
                type="text"
                placeholder="Salary, groceries, rent..."
                minLength={1}
                maxLength={255}
                required
              />
            </label>

            <label className="composer-field">
              <span>Account</span>
              <select name="account_id" defaultValue="" required>
                <option value="" disabled>
                  Select account
                </option>
                {accounts.map((account) => (
                  <option key={account.id} value={account.id}>
                    {account.name}
                  </option>
                ))}
              </select>
            </label>

            <label className="composer-field">
              <span>Category (optional)</span>
              <select name="category_id" key={transactionType} defaultValue="">
                <option value="">No category</option>
                {visibleCategories.map((category) => (
                  <option key={category.id} value={category.id}>
                    {category.name}
                  </option>
                ))}
              </select>
            </label>
          </div>
        </fieldset>

        {state.error ? <p className="composer-error">{state.error}</p> : null}

        {isSlow ? (
          <div className="composer-warning" role="status">
            <span>Still saving. This is taking longer than expected.</span>
            <button type="button" className="composer-recover" onClick={recover}>
              Reload page
            </button>
          </div>
        ) : null}

        <button type="submit" className="composer-submit" disabled={isDisabled}>
          {isPending ? "Saving..." : "Create transaction"}
        </button>
      </form>
    </section>
  );
}

export function CreateBudgetForm({ action, categories, templates }: CreateBudgetFormProps) {
  const [state, formAction, isPending] = useActionState(action, INITIAL_STATE);
  const formRef = useRef<HTMLFormElement>(null);
  const [templateBudgetId, setTemplateBudgetId] = useState("");
  const [name, setName] = useState("");
  const [amount, setAmount] = useState("");
  const [categoryId, setCategoryId] = useState("");
  const [periodStart, setPeriodStart] = useState(firstDayOfMonth());
  const [periodEnd, setPeriodEnd] = useState(lastDayOfMonth());

  const templatesById = useMemo(
    () => new Map(templates.map((template) => [template.id, template])),
    [templates],
  );

  const selectedTemplate = templateBudgetId
    ? templatesById.get(templateBudgetId) ?? null
    : null;
  const requiresCategory = !selectedTemplate;
  const isSubmitDisabled =
    isPending || (requiresCategory && categories.length === 0);

  const { isSlow, recover } = useMutationFeedback({
    state,
    isPending,
    successTitle: "Budget saved",
    defaultSuccessDescription: "Your budget guardrail is active.",
    onSuccess: () => {
      formRef.current?.reset();
      setTemplateBudgetId("");
      setName("");
      setAmount("");
      setCategoryId("");
      setPeriodStart(firstDayOfMonth());
      setPeriodEnd(lastDayOfMonth());
    },
  });

  return (
    <section className="panel composer-panel">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">New budget</p>
          <h3>Create category budget</h3>
        </div>
      </div>

      {requiresCategory && categories.length === 0 ? (
        <p className="composer-help">No expense categories available for budgeting yet.</p>
      ) : null}

      <form ref={formRef} action={formAction} className="composer-form">
        <fieldset className="composer-fieldset" disabled={isPending}>
          <input type="hidden" name="template_budget_id" value={templateBudgetId} />
          <div className="composer-grid three-columns">
            {templates.length > 0 ? (
              <label className="composer-field full-width">
                <span>Template (optional)</span>
                <select
                  value={templateBudgetId}
                  onChange={(event) => {
                    const nextTemplateId = event.target.value;
                    setTemplateBudgetId(nextTemplateId);

                    if (!nextTemplateId) {
                      setName("");
                      setAmount("");
                      setCategoryId("");
                      setPeriodStart(firstDayOfMonth());
                      setPeriodEnd(lastDayOfMonth());
                      return;
                    }

                    const template = templatesById.get(nextTemplateId);
                    if (!template) {
                      return;
                    }

                    const shiftedPeriod = shiftBudgetTemplatePeriod(
                      template.period_start,
                      template.period_end,
                    );

                    setName(template.name);
                    setAmount(template.amount);
                    setCategoryId(template.category_id ?? "");
                    setPeriodStart(shiftedPeriod.periodStart);
                    setPeriodEnd(shiftedPeriod.periodEnd);
                  }}
                >
                  <option value="">Start from scratch</option>
                  {templates.map((template) => (
                    <option key={template.id} value={template.id}>
                      {formatBudgetTemplateOption(template)}
                    </option>
                  ))}
                </select>
              </label>
            ) : null}

            <label className="composer-field full-width">
              <span>Name</span>
              <input
                name="name"
                type="text"
                placeholder="Groceries - April"
                minLength={1}
                maxLength={255}
                value={name}
                onChange={(event) => {
                  setName(event.target.value);
                }}
                required={!selectedTemplate}
              />
            </label>

            <label className="composer-field">
              <span>Amount</span>
              <input
                name="amount"
                type="number"
                placeholder="0.00"
                min="0.01"
                step="0.01"
                value={amount}
                onChange={(event) => {
                  setAmount(event.target.value);
                }}
                required={!selectedTemplate}
              />
            </label>

            {requiresCategory ? (
              <label className="composer-field">
                <span>Category</span>
                <select
                  name="category_id"
                  value={categoryId}
                  onChange={(event) => {
                    setCategoryId(event.target.value);
                  }}
                  required
                >
                  <option value="" disabled>
                    Select category
                  </option>
                  {categories.map((category) => (
                    <option key={category.id} value={category.id}>
                      {category.name}
                    </option>
                  ))}
                </select>
              </label>
            ) : (
              <p className="composer-help">
                Template category target: {selectedTemplate?.category_name ?? "Template default"}
              </p>
            )}

            <label className="composer-field">
              <span>Start date</span>
              <input
                name="period_start"
                type="date"
                value={periodStart}
                onChange={(event) => {
                  setPeriodStart(event.target.value);
                }}
                required
              />
            </label>

            <label className="composer-field">
              <span>End date</span>
              <input
                name="period_end"
                type="date"
                value={periodEnd}
                onChange={(event) => {
                  setPeriodEnd(event.target.value);
                }}
                required
              />
            </label>
          </div>
        </fieldset>

        {state.error ? <p className="composer-error">{state.error}</p> : null}

        {isSlow ? (
          <div className="composer-warning" role="status">
            <span>Still saving. This is taking longer than expected.</span>
            <button type="button" className="composer-recover" onClick={recover}>
              Reload page
            </button>
          </div>
        ) : null}

        <button type="submit" className="composer-submit" disabled={isSubmitDisabled}>
          {isPending
            ? "Saving..."
            : selectedTemplate
              ? "Create from template"
              : "Create budget"}
        </button>
      </form>
    </section>
  );
}

export function CreateRecurringRuleForm({
  action,
  accounts,
}: CreateRecurringRuleFormProps) {
  const [state, formAction, isPending] = useActionState(action, INITIAL_STATE);
  const [frequency, setFrequency] = useState<RecurringFrequency>("monthly");
  const [interval, setIntervalValue] = useState("1");
  const [startDate, setStartDate] = useState(todayIsoDate());
  const [endDate, setEndDate] = useState("");
  const [weekendAdjustment, setWeekendAdjustment] = useState<WeekendAdjustment>("keep");
  const formRef = useRef<HTMLFormElement>(null);
  const isDisabled = accounts.length === 0 || isPending;

  const previewDates = useMemo(
    () =>
      buildRecurringPreviewDates({
        startDate,
        endDate,
        frequency,
        intervalRaw: interval,
        weekendAdjustment,
      }),
    [endDate, frequency, interval, startDate, weekendAdjustment],
  );

  const { isSlow, recover } = useMutationFeedback({
    state,
    isPending,
    successTitle: "Recurring rule saved",
    defaultSuccessDescription: "Future projections will include this expense.",
    onSuccess: () => {
      formRef.current?.reset();
      setFrequency("monthly");
      setIntervalValue("1");
      setStartDate(todayIsoDate());
      setEndDate("");
      setWeekendAdjustment("keep");
    },
  });

  return (
    <section className="panel composer-panel">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">New recurring expense</p>
          <h3>Create rule for future bills</h3>
        </div>
      </div>

      {accounts.length === 0 ? (
        <p className="composer-help">Create an account first to add recurring expenses.</p>
      ) : null}

      <form ref={formRef} action={formAction} className="composer-form">
        <fieldset className="composer-fieldset" disabled={isDisabled}>
          <div className="composer-grid three-columns">
            <label className="composer-field full-width">
              <span>Description</span>
              <input
                name="description"
                type="text"
                placeholder="Rent, internet, gym..."
                minLength={1}
                maxLength={255}
                required
              />
            </label>

            <label className="composer-field">
              <span>Amount</span>
              <input
                name="amount"
                type="number"
                min="0.01"
                step="0.01"
                placeholder="0.00"
                required
              />
            </label>

            <label className="composer-field">
              <span>Account</span>
              <select name="account_id" defaultValue="" required>
                <option value="" disabled>
                  Select account
                </option>
                {accounts.map((account) => (
                  <option key={account.id} value={account.id}>
                    {account.name}
                  </option>
                ))}
              </select>
            </label>

            <label className="composer-field">
              <span>Frequency</span>
              <select
                name="frequency"
                value={frequency}
                onChange={(event) => {
                  const nextValue = event.target.value;
                  if (
                    nextValue === "daily" ||
                    nextValue === "weekly" ||
                    nextValue === "monthly" ||
                    nextValue === "yearly"
                  ) {
                    setFrequency(nextValue);
                  }
                }}
                required
              >
                <option value="daily">Daily</option>
                <option value="weekly">Weekly</option>
                <option value="monthly">Monthly</option>
                <option value="yearly">Yearly</option>
              </select>
            </label>

            <label className="composer-field">
              <span>Interval</span>
              <input
                name="interval"
                type="number"
                min="1"
                step="1"
                value={interval}
                onChange={(event) => {
                  setIntervalValue(event.target.value);
                }}
                required
              />
            </label>

            <label className="composer-field">
              <span>Start date</span>
              <input
                name="start_date"
                type="date"
                value={startDate}
                onChange={(event) => {
                  setStartDate(event.target.value);
                }}
                required
              />
            </label>

            <label className="composer-field">
              <span>End date (optional)</span>
              <input
                name="end_date"
                type="date"
                value={endDate}
                onChange={(event) => {
                  setEndDate(event.target.value);
                }}
              />
            </label>

            <label className="composer-field">
              <span>Weekend rule</span>
              <select
                name="weekend_adjustment"
                value={weekendAdjustment}
                onChange={(event) => {
                  const nextValue = event.target.value;
                  if (
                    nextValue === "keep" ||
                    nextValue === "following" ||
                    nextValue === "preceding"
                  ) {
                    setWeekendAdjustment(nextValue);
                  }
                }}
                required
              >
                <option value="keep">Keep same date</option>
                <option value="following">Move to Monday</option>
                <option value="preceding">Move to Friday</option>
              </select>
            </label>
          </div>
        </fieldset>

        {previewDates.length > 0 ? (
          <div className="composer-preview" aria-live="polite">
            <p className="eyebrow">Preview</p>
            <h4>Next occurrences</h4>
            <ul>
              {previewDates.map((item) => (
                <li key={item.isoDate}>
                  <span>{item.label}</span>
                  <strong>{item.isoDate}</strong>
                </li>
              ))}
            </ul>
          </div>
        ) : null}

        {state.error ? <p className="composer-error">{state.error}</p> : null}

        {isSlow ? (
          <div className="composer-warning" role="status">
            <span>Still saving. This is taking longer than expected.</span>
            <button type="button" className="composer-recover" onClick={recover}>
              Reload page
            </button>
          </div>
        ) : null}

        <button type="submit" className="composer-submit" disabled={isDisabled}>
          {isPending ? "Saving..." : "Create recurring expense"}
        </button>
      </form>
    </section>
  );
}
