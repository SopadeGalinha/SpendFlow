import { FeatureEmptyState } from "@/components/feature-empty-state";
import { CalendarWorkspace } from "@/components/calendar-workspace";
import {
  buildRecurringProjectionViews,
  formatCurrency,
  formatMonthLabel,
} from "@/lib/finance-selectors";
import type {
  AccountResponse,
  ProjectionResponse,
  RecurringRuleResponse,
  TransactionResponse,
} from "@/lib/mock-finance";

type CalendarContentProps = {
  accounts: AccountResponse[];
  transactions: TransactionResponse[];
  recurringRules: RecurringRuleResponse[];
  projections: ProjectionResponse[];
};

export function CalendarContent({
  accounts,
  transactions,
  recurringRules,
  projections,
}: CalendarContentProps) {
  const projectionViews = buildRecurringProjectionViews(
    projections,
    transactions,
    undefined,
    recurringRules,
  );

  if (projectionViews.length === 0) {
    return (
      <FeatureEmptyState
        eyebrow="Calendar"
        title="No projected recurring items yet"
        description="Once recurring rules exist on the backend, this calendar workspace will show upcoming scheduled bills by month."
      />
    );
  }

  const groupedByMonth = Object.entries(
    projectionViews.reduce<Record<string, typeof projectionViews>>((accumulator, projection) => {
      accumulator[projection.monthKey] = [
        ...(accumulator[projection.monthKey] ?? []),
        projection,
      ];
      return accumulator;
    }, {}),
  ).sort(([left], [right]) => left.localeCompare(right));

  const unpaidTotal = projectionViews
    .filter((projection) => projection.state !== "paid")
    .reduce((sum, projection) => sum + projection.amount, 0);

  const today = new Date();
  today.setHours(0, 0, 0, 0);

  const soonDate = new Date(today);
  soonDate.setDate(soonDate.getDate() + 30);

  const nextThirtyDaysDue = projectionViews
    .filter((projection) => {
      if (projection.state === "paid") {
        return false;
      }

      const projectionDate = new Date(`${projection.date}T00:00:00`);
      return projectionDate >= today && projectionDate <= soonDate;
    })
    .reduce((sum, projection) => sum + projection.amount, 0);

  const accountNames = Object.fromEntries(accounts.map((account) => [account.id, account.name]));

  return (
    <>
      <section className="hero-panel placeholder-hero">
        <div>
          <p className="eyebrow">Calendar</p>
          <h2>Recurring calendar workspace</h2>
          <p className="hero-copy">
            This route now includes the same day-level calendar interaction available in the dashboard, plus a short-horizon view of upcoming obligations.
          </p>
        </div>
        <div className="hero-stats">
          <div>
            <span>Visible months</span>
            <strong>{groupedByMonth.length}</strong>
          </div>
          <div>
            <span>Unpaid scheduled</span>
            <strong>{formatCurrency(unpaidTotal)}</strong>
          </div>
          <div>
            <span>Due in 30 days</span>
            <strong>{formatCurrency(nextThirtyDaysDue)}</strong>
          </div>
        </div>
      </section>

      <CalendarWorkspace
        accounts={accounts}
        transactions={transactions}
        recurringRules={recurringRules}
        projections={projections}
        panelEyebrow="Calendar"
        panelTitle="Day planner and bill confirmations"
      />

      <section className="calendar-route-grid">
        {groupedByMonth.map(([monthKey, items]) => {
          const monthTotal = items.reduce((sum, item) => sum + item.amount, 0);
          return (
            <article key={monthKey} className="panel calendar-month-panel">
              <div className="panel-heading">
                <div>
                  <p className="eyebrow">{formatMonthLabel(monthKey)}</p>
                  <h3>{items.length} scheduled items</h3>
                </div>
                <span className="pill">{formatCurrency(monthTotal)}</span>
              </div>
              <div className="recurring-list">
                {items.map((projection) => (
                  <div key={projection.id} className="recurring-row">
                    <div>
                      <strong>{projection.name}</strong>
                      <span>
                        {new Date(`${projection.date}T00:00:00`).toLocaleDateString("en-US", {
                          month: "short",
                          day: "numeric",
                        })} · {accountNames[projection.accountId] ?? "Linked account"}
                      </span>
                    </div>
                    <div>
                      <strong>{formatCurrency(projection.amount)}</strong>
                      <span>Original {formatCurrency(projection.originalAmount)}</span>
                    </div>
                    <div className="recurring-row-meta">
                      <span className={`recurring-type ${projection.tone}`}>{projection.tone}</span>
                      <span className={`bill-status ${projection.state}`}>{projection.state}</span>
                    </div>
                  </div>
                ))}
              </div>
            </article>
          );
        })}
      </section>
    </>
  );
}