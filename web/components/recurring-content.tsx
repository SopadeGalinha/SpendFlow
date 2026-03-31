import { FeatureEmptyState } from "@/components/feature-empty-state";
import { CreateRecurringRuleForm } from "@/components/finance-forms";
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
import type { FinanceActionState } from "@/app/finance-actions";

type RecurringContentProps = {
  accounts: AccountResponse[];
  recurringRules: RecurringRuleResponse[];
  projections: ProjectionResponse[];
  transactions: TransactionResponse[];
  createRecurringRuleAction: (
    state: FinanceActionState,
    formData: FormData,
  ) => Promise<FinanceActionState>;
};

export function RecurringContent({
  accounts,
  recurringRules,
  projections,
  transactions,
  createRecurringRuleAction,
}: RecurringContentProps) {
  const upcoming = buildRecurringProjectionViews(
    projections,
    transactions,
    undefined,
    recurringRules,
  ).slice(0, 18);

  if (recurringRules.length === 0) {
    return (
      <>
        <CreateRecurringRuleForm
          action={createRecurringRuleAction}
          accounts={accounts}
        />
        <FeatureEmptyState
          eyebrow="Recurring"
          title="No recurring rules yet"
          description="Create your first recurring expense rule to start projections in the recurring and calendar views."
        />
      </>
    );
  }

  const paidCount = upcoming.filter((item) => item.state === "paid").length;
  const unpaidCount = upcoming.filter((item) => item.state !== "paid").length;

  return (
    <>
      <CreateRecurringRuleForm
        action={createRecurringRuleAction}
        accounts={accounts}
      />

      <section className="hero-panel placeholder-hero">
        <div>
          <p className="eyebrow">Recurring</p>
          <h2>Rules and upcoming projections</h2>
          <p className="hero-copy">
            This route now combines recurring rules with projected scheduled items from the authenticated backend so you can review both the templates and their upcoming impact.
          </p>
        </div>
        <div className="hero-stats">
          <div>
            <span>Rules</span>
            <strong>{recurringRules.length}</strong>
          </div>
          <div>
            <span>Upcoming unpaid</span>
            <strong>{unpaidCount}</strong>
          </div>
        </div>
      </section>

      <section className="two-column">
        <article className="panel">
          <div className="panel-heading">
            <div>
              <p className="eyebrow">Rules</p>
              <h3>Recurring templates</h3>
            </div>
            <span className="pill">{paidCount} already paid in visible list</span>
          </div>
          <div className="recurring-list">
            {recurringRules.map((rule) => (
              <div key={rule.id} className="recurring-row">
                <div>
                  <strong>{rule.description}</strong>
                  <span>
                    {rule.frequency} · starts {new Date(`${rule.start_date}T00:00:00`).toLocaleDateString("en-US", {
                      month: "short",
                      day: "numeric",
                    })}
                  </span>
                </div>
                <div>
                  <strong>{formatCurrency(Number(rule.amount))}</strong>
                  <span>{rule.weekend_adjustment} weekend rule</span>
                </div>
              </div>
            ))}
          </div>
        </article>

        <article className="panel">
          <div className="panel-heading">
            <div>
              <p className="eyebrow">Upcoming</p>
              <h3>Projected bills</h3>
            </div>
            <span className="pill">Next 18 scheduled items</span>
          </div>
          <div className="recurring-list">
            {upcoming.map((projection) => (
              <div key={projection.id} className="recurring-row">
                <div>
                  <strong>{projection.name}</strong>
                  <span>
                    {formatMonthLabel(projection.monthKey)} · {new Date(`${projection.date}T00:00:00`).toLocaleDateString("en-US", {
                      month: "short",
                      day: "numeric",
                    })}
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
      </section>
    </>
  );
}