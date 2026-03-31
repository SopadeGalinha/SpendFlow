import { AppShell } from "@/components/app-shell";
import { getCurrentUserProfile } from "@/lib/auth";

type AppShellServerProps = {
  children: React.ReactNode;
};

export async function AppShellServer({ children }: AppShellServerProps) {
  const currentUser = await getCurrentUserProfile();

  return <AppShell currentUser={currentUser}>{children}</AppShell>;
}
