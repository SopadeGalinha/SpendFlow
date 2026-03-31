import { FeatureEmptyState } from "@/components/feature-empty-state";
import { CreateTransactionForm } from "@/components/finance-forms";
import { TransactionsWorkbench } from "@/components/transactions-workbench";
import { buildRecentTransactionViews, formatCurrency } from "@/lib/finance-selectors";
import type { AccountResponse, TransactionResponse } from "@/lib/mock-finance";
import type { CategoryResponse } from "@/lib/finance-client";
import type { FinanceActionState } from "@/app/finance-actions";

type TransactionsContentProps = {
  transactions: TransactionResponse[];
  accounts: AccountResponse[];
  incomeCategories: CategoryResponse[];
  expenseCategories: CategoryResponse[];
  createTransactionAction: (
    state: FinanceActionState,
    formData: FormData,
  ) => Promise<FinanceActionState>;
  bulkUpdateTransactionsAction: (
    state: FinanceActionState,
    formData: FormData,
  ) => Promise<FinanceActionState>;
};

export function TransactionsContent({
  transactions,
  accounts,
  incomeCategories,
  expenseCategories,
  createTransactionAction,
  bulkUpdateTransactionsAction,
}: TransactionsContentProps) {
  const views = buildRecentTransactionViews(transactions, accounts, 18);
  const income = transactions
    .filter((transaction) => transaction.type === "income")
    .reduce((sum, transaction) => sum + Number(transaction.amount), 0);
  const expenses = transactions
    .filter((transaction) => transaction.type === "expense")
    .reduce((sum, transaction) => sum + Number(transaction.amount), 0);

  if (transactions.length === 0) {
    return (
      <>
        <CreateTransactionForm
          action={createTransactionAction}
          accounts={accounts}
          incomeCategories={incomeCategories}
          expenseCategories={expenseCategories}
        />
        <FeatureEmptyState
          eyebrow="Transactions"
          title="No ledger entries yet"
          description="Add your first income or expense entry to populate this ledger view."
        />
      </>
    );
  }

  return (
    <>
      <CreateTransactionForm
        action={createTransactionAction}
        accounts={accounts}
        incomeCategories={incomeCategories}
        expenseCategories={expenseCategories}
      />

      <TransactionsWorkbench
        transactions={transactions}
        accounts={accounts}
        categories={[...incomeCategories, ...expenseCategories]}
        bulkUpdateAction={bulkUpdateTransactionsAction}
      />

      <section className="hero-panel placeholder-hero">
        <div>
          <p className="eyebrow">Transactions</p>
          <h2>Ledger-first transaction review</h2>
          <p className="hero-copy">
            This page is now showing real mock ledger data in the same shape as the API contract, which gives us a stable base for search, filters, and review flows.
          </p>
        </div>
        <div className="hero-stats">
          <div>
            <span>Total income</span>
            <strong>{formatCurrency(income)}</strong>
          </div>
          <div>
            <span>Total expenses</span>
            <strong>{formatCurrency(expenses)}</strong>
          </div>
        </div>
      </section>

      <section className="panel wide-panel">
        <div className="panel-heading">
          <div>
            <p className="eyebrow">Recent activity</p>
            <h3>Last 18 ledger entries</h3>
          </div>
          <span className="pill">Contract-backed list view</span>
        </div>
        <div className="activity-list">
          {views.map((item) => (
            <div key={item.id} className="activity-row">
              <div>
                <strong>{item.title}</strong>
                <span>{item.subtitle}</span>
              </div>
              <span className={`amount ${item.kind}`}>{item.amountLabel}</span>
            </div>
          ))}
        </div>
      </section>
    </>
  );
}