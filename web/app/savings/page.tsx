import { AppShellServer } from "@/components/app-shell-server";
import { SavingsContent } from "@/components/savings-content";
import { getFinanceDataset } from "@/lib/finance-client";

export default async function SavingsPage() {
  const dataset = await getFinanceDataset();

  return (
    <AppShellServer>
      <SavingsContent
        accounts={dataset.accounts}
        transactions={dataset.transactions}
        projections={dataset.projections}
      />
    </AppShellServer>
  );
}