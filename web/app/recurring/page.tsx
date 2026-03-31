import { createRecurringRuleAction } from "@/app/finance-actions";
import { AppShellServer } from "@/components/app-shell-server";
import { RecurringContent } from "@/components/recurring-content";
import { getAccounts, getRecurringWorkspaceData } from "@/lib/finance-client";

export default async function RecurringPage() {
  const [dataset, accounts] = await Promise.all([
    getRecurringWorkspaceData(6),
    getAccounts(),
  ]);

  return (
    <AppShellServer>
      <RecurringContent
        accounts={accounts}
        recurringRules={dataset.recurringRules}
        projections={dataset.projections}
        transactions={dataset.transactions}
        createRecurringRuleAction={createRecurringRuleAction}
      />
    </AppShellServer>
  );
}