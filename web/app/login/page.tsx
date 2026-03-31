import { loginAction } from "@/app/auth-actions";
import { AuthForm } from "@/components/auth-form";

export default function LoginPage() {
  return (
    <AuthForm
      title="Sign in to SpendFlow"
      description="Use your backend account to unlock authenticated account and transaction data. This is the first real token-backed path through the app."
      submitLabel="Sign in"
      alternateLabel="Need an account?"
      alternateHref="/register"
      alternateText="Create one"
      action={loginAction}
      fields={[
        {
          name: "email",
          label: "Email",
          type: "email",
          placeholder: "you@example.com",
          autoComplete: "email",
        },
        {
          name: "password",
          label: "Password",
          type: "password",
          placeholder: "At least 8 characters",
          autoComplete: "current-password",
        },
      ]}
    />
  );
}
