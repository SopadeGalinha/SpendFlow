import { AppShellServer } from "@/components/app-shell-server";
import { CalendarContent } from "@/components/calendar-content";
import { getCalendarWorkspaceData } from "@/lib/finance-client";

export default async function CalendarPage() {
  const dataset = await getCalendarWorkspaceData(4);

  return (
    <AppShellServer>
      <CalendarContent
        accounts={dataset.accounts}
        transactions={dataset.transactions}
        recurringRules={dataset.recurringRules}
        projections={dataset.projections}
      />
    </AppShellServer>
  );
}