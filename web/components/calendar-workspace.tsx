"use client";

import { useEffect, useRef, useState } from "react";

import type {
  AccountResponse,
  ProjectionResponse,
  RecurringRuleResponse,
  TransactionResponse,
} from "@/lib/mock-finance";
import { emitShellToast } from "@/lib/ui-feedback";

const WEEKDAY_LABELS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
const MAX_VISIBLE_DAY_ITEMS = 2;
const INITIAL_MONTH = new Date(new Date().getFullYear(), new Date().getMonth(), 1);

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

type CalendarWorkspaceProps = {
  accounts: AccountResponse[];
  transactions: TransactionResponse[];
  recurringRules: RecurringRuleResponse[];
  projections: ProjectionResponse[];
  panelEyebrow?: string;
  panelTitle?: string;
  panelId?: string;
};

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

function formatRelativeMonth(monthKey: string) {
  const [year, month] = monthKey.split("-").map(Number);
  return new Date(year, month - 1, 1).toLocaleDateString("en-US", {
    month: "long",
    year: "numeric",
  });
}

function shiftMonth(baseDate: Date, monthOffset: number) {
  return new Date(baseDate.getFullYear(), baseDate.getMonth() + monthOffset, 1);
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

function buildCalendarBills(args: {
  monthKey?: string;
  projections: ProjectionResponse[];
  recurringRules: RecurringRuleResponse[];
  transactions: TransactionResponse[];
}) {
  const today = new Date();
  today.setHours(0, 0, 0, 0);

  return args.projections
    .filter((projection) =>
      args.monthKey ? projection.date.startsWith(args.monthKey) : true,
    )
    .reduce<CalendarBill[]>((accumulator, projection) => {
      const rule = args.recurringRules.find((item) => item.id === projection.rule_id);
      if (!rule) {
        return accumulator;
      }

      const matchingTransaction = args.transactions.find(
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
        id: `${projection.date}-${projection.rule_id}`,
        projectionId: projection.id,
        name: projection.description,
        cadence: "Monthly",
        tone: getBillTone(projection.rule_id),
        type: projection.type,
        date: projectedDate,
        monthKey: projection.date.slice(0, 7),
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

function totalUpcomingWithinDays(unpaidBills: CalendarBill[], days: number) {
  const today = new Date();
  today.setHours(0, 0, 0, 0);

  const horizon = new Date(today);
  horizon.setDate(horizon.getDate() + days);
  horizon.setHours(23, 59, 59, 999);

  return unpaidBills
    .filter((bill) => bill.date >= today && bill.date <= horizon)
    .reduce((sum, bill) => sum + bill.expectedAmount, 0);
}

export function CalendarWorkspace({
  accounts,
  transactions,
  recurringRules,
  projections,
  panelEyebrow = "Calendar",
  panelTitle = "Recurring view",
  panelId = "calendar",
}: CalendarWorkspaceProps) {
  const modalRef = useRef<HTMLElement | null>(null);
  const [calendarMonth, setCalendarMonth] = useState(INITIAL_MONTH);
  const [transactionsState, setTransactionsState] = useState(transactions);
  const [selectedDayKey, setSelectedDayKey] = useState<string | null>(null);
  const [payingBillId, setPayingBillId] = useState<string | null>(null);
  const [paymentAmount, setPaymentAmount] = useState("");

  const monthKey = formatMonthKey(calendarMonth);
  const monthBills = buildCalendarBills({
    monthKey,
    projections,
    recurringRules,
    transactions: transactionsState,
  });
  const calendarDays = buildCalendarDays(calendarMonth, monthBills);
  const selectedDay = calendarDays.find((day) => day.key === selectedDayKey) ?? null;
  const accountNames = Object.fromEntries(
    accounts.map((account) => [account.id, account.name]),
  );

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
  const calendarLabel = formatRelativeMonth(monthKey);

  const allUpcomingUnpaid = buildCalendarBills({
    projections,
    recurringRules,
    transactions: transactionsState,
  }).filter((bill) => bill.status !== "paid");
  const dueIn30Days = totalUpcomingWithinDays(allUpcomingUnpaid, 30);
  const dueIn60Days = totalUpcomingWithinDays(allUpcomingUnpaid, 60);

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
    setPayingBillId(null);
    setPaymentAmount("");

    emitShellToast({
      level: "success",
      title: "Payment captured",
      description: `${bill.name} was marked as paid.`,
    });
  }

  return (
    <>
      <section className="panel wide-panel" id={panelId}>
        <div className="panel-heading calendar-heading">
          <div>
            <p className="eyebrow">{panelEyebrow}</p>
            <h3>{panelTitle}</h3>
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
            <div className="calendar-summary">
              <span>Due in 30 days</span>
              <strong>{formatCurrency(dueIn30Days)}</strong>
            </div>
            <div className="calendar-summary">
              <span>Due in 60 days</span>
              <strong>{formatCurrency(dueIn60Days)}</strong>
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

            <section className="panel">
              <div className="panel-heading">
                <div>
                  <p className="eyebrow">Accounts</p>
                  <h3>Available payment sources</h3>
                </div>
              </div>
              <div className="account-list">
                {accounts.map((account) => (
                  <div key={account.id} className="account-row">
                    <div>
                      <strong>{account.name}</strong>
                      <span>
                        {account.account_type === "checking"
                          ? "Daily cash account"
                          : "Savings bucket"}
                      </span>
                    </div>
                    <strong>{formatCurrency(parseAmount(account.balance))}</strong>
                  </div>
                ))}
              </div>
            </section>

            <section className="panel">
              <div className="panel-heading">
                <div>
                  <p className="eyebrow">Context</p>
                  <h3>Scheduled items for this day</h3>
                </div>
              </div>
              <div className="activity-list">
                {selectedDay.bills.map((bill) => (
                  <div key={`${bill.id}-context`} className="activity-row">
                    <div>
                      <strong>{bill.name}</strong>
                      <span>
                        {bill.cadence} · {accountNames[bill.accountId] ?? "Linked account"}
                      </span>
                    </div>
                    <span className="amount expense">-{formatCurrency(bill.expectedAmount)}</span>
                  </div>
                ))}
              </div>
            </section>
          </section>
        </div>
      ) : null}
    </>
  );
}
