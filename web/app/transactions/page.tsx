import { bulkUpdateTransactionsAction, createTransactionAction } from "@/app/finance-actions";
import { AppShellServer } from "@/components/app-shell-server";
import { TransactionsContent } from "@/components/transactions-content";
import { getAccounts, getCategories, getTransactions } from "@/lib/finance-client";

export default async function TransactionsPage() {
  const [transactions, accounts, incomeCategories, expenseCategories] = await Promise.all([
    getTransactions(),
    getAccounts(),
    getCategories("income"),
    getCategories("expense"),
  ]);

  return (
    <AppShellServer>
      <TransactionsContent
        transactions={transactions}
        accounts={accounts}
        incomeCategories={incomeCategories}
        expenseCategories={expenseCategories}
        createTransactionAction={createTransactionAction}
        bulkUpdateTransactionsAction={bulkUpdateTransactionsAction}
      />
    </AppShellServer>
  );
}