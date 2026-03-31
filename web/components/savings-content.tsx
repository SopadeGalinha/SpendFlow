import { FeatureEmptyState } from "@/components/feature-empty-state";
import {
  buildSavingsPlan,
  formatCurrency,
} from "@/lib/finance-selectors";
import type {
  AccountResponse,
  ProjectionResponse,
  TransactionResponse,
} from "@/lib/mock-finance";

type SavingsContentProps = {
  accounts: AccountResponse[];
  transactions: TransactionResponse[];
  projections: ProjectionResponse[];
};

function formatRunway(months: number) {
  if (!Number.isFinite(months) || months <= 0) {
    return "No runway yet";
  }

  return `${months.toFixed(1)} months`;
}

export function SavingsContent({
  accounts,
  transactions,
  projections,
}: SavingsContentProps) {
  const plan = buildSavingsPlan(accounts, transactions, projections);

  if (plan.savingsAccounts.length === 0) {
    return (
      <FeatureEmptyState
        eyebrow="Savings"
        title="No savings accounts tracked yet"
        description="Add a savings account on the backend and this view will turn into reserve tracking, runway, and contribution pacing automatically."
      />
    );
  }

  const reserveProgress =
    plan.reserveTarget > 0
      ? Math.min((plan.totalSavings / plan.reserveTarget) * 100, 100)
      : 0;

  return (
    <>
      <section className="hero-panel placeholder-hero">
        <div>
          <p className="eyebrow">Savings</p>
          <h2>Reserve strength and contribution pace</h2>
          <p className="hero-copy">
            This view uses live balances plus recent cashflow to show how much buffer is actually in place, not just how much sits in a savings account.
          </p>
        </div>
        <div className="hero-stats">
          <div>
            <span>Total reserves</span>
            <strong>{formatCurrency(plan.totalSavings)}</strong>
          </div>
          <div>
            <span>Runway at current baseline</span>
            <strong>{formatRunway(plan.runwayMonths)}</strong>
          </div>
        </div>
      </section>

      <section className="panel wide-panel savings-grid">
        <article className="panel savings-panel">
          <div className="panel-heading">
            <div>
              <p className="eyebrow">Buckets</p>
              <h3>Where reserves are parked</h3>
            </div>
            <span className="pill">{plan.savingsAccounts.length} savings accounts</span>
          </div>
          <div className="account-list">
            {plan.savingsAccounts.map((account) => (
              <div key={account.id} className="account-row">
                <div>
                  <strong>{account.name}</strong>
                  <span>{account.share}% of tracked reserves</span>
                </div>
                <div>
                  <strong>{formatCurrency(account.balanceValue)}</strong>
                  <span>{account.accountLabel}</span>
                </div>
              </div>
            ))}
          </div>
        </article>

        <article className="panel savings-panel">
          <div className="panel-heading">
            <div>
              <p className="eyebrow">Target</p>
              <h3>Six-month reserve posture</h3>
            </div>
            <span className="pill">
              {plan.reserveTarget > 0
                ? `${Math.round(reserveProgress)}% funded`
                : "Target pending"}
            </span>
          </div>
          <div className="savings-metric-stack">
            <div className="savings-metric-card">
              <span>Six-month reserve target</span>
              <strong>
                {plan.reserveTarget > 0
                  ? formatCurrency(plan.reserveTarget)
                  : "Need more spend history"}
              </strong>
            </div>
            <div className="savings-metric-card">
              <span>Average monthly net</span>
              <strong>{formatCurrency(plan.averageNet)}</strong>
            </div>
            <div className="savings-progress" aria-hidden="true">
              <span style={{ width: `${reserveProgress}%` }} />
            </div>
            <p className="savings-copy">
              Baseline monthly spend is estimated from current recurring obligations when available, otherwise from recent monthly expenses.
            </p>
          </div>
        </article>
      </section>

      <section className="panel wide-panel">
        <div className="panel-heading">
          <div>
            <p className="eyebrow">Pace</p>
            <h3>Recent monthly savings rhythm</h3>
          </div>
          <span className="pill">Last {plan.monthlyCashflow.length} months</span>
        </div>
        <div className="savings-cashflow-list">
          {plan.monthlyCashflow.map((month) => (
            <div key={month.monthKey} className="savings-cashflow-row">
              <div>
                <strong>{month.label}</strong>
                <span>
                  Income {formatCurrency(month.income)} · Expenses {formatCurrency(month.expenses)}
                </span>
              </div>
              <span className={month.net >= 0 ? "amount income" : "amount expense"}>
                {month.net >= 0 ? "+" : "-"}
                {formatCurrency(Math.abs(month.net))}
              </span>
            </div>
          ))}
        </div>
      </section>
    </>
  );
}
