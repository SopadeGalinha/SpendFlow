import { AppShell } from "@/components/app-shell";
import { DashboardContent } from "@/components/dashboard-content";
import { getCurrentUserProfile } from "@/lib/auth";
import { getFinanceDataset } from "@/lib/finance-client";

export async function DashboardShell() {
  const [dataset, currentUser] = await Promise.all([
    getFinanceDataset(),
    getCurrentUserProfile(),
  ]);

  return (
    <AppShell currentUser={currentUser}>
      <DashboardContent initialDataset={dataset} greetingName={currentUser.username} />
    </AppShell>
  );
}
