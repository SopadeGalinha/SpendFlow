import { createBudgetAction } from "@/app/finance-actions";
import { AppShellServer } from "@/components/app-shell-server";
import { BudgetContent } from "@/components/budget-content";
import { getBudgetsByPeriod, getCategories } from "@/lib/finance-client";

export default async function BudgetPage() {
  const currentMonthKey = new Date().toISOString().slice(0, 7);
  const currentYear = Number(currentMonthKey.slice(0, 4));

  const [budgets, expenseCategories] = await Promise.all([
    getBudgetsByPeriod({ year: currentYear }),
    getCategories("expense"),
  ]);

  return (
    <AppShellServer>
      <BudgetContent
        budgets={budgets}
        monthKey={currentMonthKey}
        expenseCategories={expenseCategories}
        createBudgetAction={createBudgetAction}
      />
    </AppShellServer>
  );
}