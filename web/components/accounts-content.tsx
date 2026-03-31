import { FeatureEmptyState } from "@/components/feature-empty-state";
import { CreateAccountForm } from "@/components/finance-forms";
import { buildAccountSummaries, formatCurrency } from "@/lib/finance-selectors";
import type { AccountResponse } from "@/lib/mock-finance";
import type { FinanceActionState } from "@/app/finance-actions";

type AccountsContentProps = {
  accounts: AccountResponse[];
  createAccountAction: (
    state: FinanceActionState,
    formData: FormData,
  ) => Promise<FinanceActionState>;
};

export function AccountsContent({
  accounts,
  createAccountAction,
}: AccountsContentProps) {
  const summaries = buildAccountSummaries(accounts);
  const totalBalance = summaries.reduce((sum, account) => sum + account.balanceValue, 0);
  const liquidCash = summaries
    .filter((account) => account.account_type === "checking")
    .reduce((sum, account) => sum + account.balanceValue, 0);

  if (accounts.length === 0) {
    return (
      <>
        <CreateAccountForm action={createAccountAction} />
        <FeatureEmptyState
          eyebrow="Accounts"
          title="No accounts connected yet"
          description="Create your first checking or savings account to start tracking balances and allocations."
        />
      </>
    );
  }

  return (
    <>
      <CreateAccountForm action={createAccountAction} />

      <section className="hero-panel placeholder-hero">
        <div>
          <p className="eyebrow">Accounts</p>
          <h2>Account balances and allocation</h2>
          <p className="hero-copy">
            This screen is now driven by the same contract-shaped data that the backend will return, so connection work becomes transport wiring instead of UI rework.
          </p>
        </div>
        <div className="hero-stats">
          <div>
            <span>Total balances</span>
            <strong>{formatCurrency(totalBalance)}</strong>
          </div>
          <div>
            <span>Liquid cash</span>
            <strong>{formatCurrency(liquidCash)}</strong>
          </div>
        </div>
      </section>

      <section className="panel wide-panel">
        <div className="panel-heading">
          <div>
            <p className="eyebrow">Holdings</p>
            <h3>Where money sits today</h3>
          </div>
          <span className="pill">{accounts.length} active accounts</span>
        </div>
        <div className="account-list">
          {summaries.map((account) => (
            <div key={account.id} className="account-row">
              <div>
                <strong>{account.name}</strong>
                <span>{account.accountLabel}</span>
              </div>
              <div>
                <strong>{formatCurrency(account.balanceValue)}</strong>
                <span>{account.allocation}% of tracked balances</span>
              </div>
            </div>
          ))}
        </div>
      </section>
    </>
  );
}