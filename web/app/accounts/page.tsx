import { createAccountAction } from "@/app/finance-actions";
import { AppShellServer } from "@/components/app-shell-server";
import { AccountsContent } from "@/components/accounts-content";
import { getAccounts } from "@/lib/finance-client";

export default async function AccountsPage() {
  const accounts = await getAccounts();

  return (
    <AppShellServer>
      <AccountsContent
        accounts={accounts}
        createAccountAction={createAccountAction}
      />
    </AppShellServer>
  );
}