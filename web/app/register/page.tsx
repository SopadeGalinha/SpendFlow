import { registerAction } from "@/app/auth-actions";
import { AuthForm } from "@/components/auth-form";

export default function RegisterPage() {
  return (
    <AuthForm
      title="Create your SpendFlow account"
      description="Register against the real backend, then the frontend signs you in immediately and stores the returned JWT in a secure session cookie."
      submitLabel="Create account"
      alternateLabel="Already have an account?"
      alternateHref="/login"
      alternateText="Sign in"
      action={registerAction}
      fields={[
        {
          name: "username",
          label: "Username",
          type: "text",
          placeholder: "your-name",
          autoComplete: "username",
        },
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
          autoComplete: "new-password",
        },
        {
          name: "city",
          label: "City",
          type: "text",
          placeholder: "Porto",
          autoComplete: "address-level2",
          optional: true,
        },
      ]}
    />
  );
}
