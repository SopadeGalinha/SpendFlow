"use client";

import Link from "next/link";
import { useActionState } from "react";

import type { AuthActionState } from "@/app/auth-actions";

type AuthFormField = {
  name: string;
  label: string;
  type: "text" | "email" | "password";
  placeholder: string;
  autoComplete?: string;
  optional?: boolean;
};

type AuthFormProps = {
  title: string;
  description: string;
  notice?: string | null;
  submitLabel: string;
  alternateLabel: string;
  alternateHref: "/login" | "/register";
  alternateText: string;
  fields: AuthFormField[];
  action: (
    state: AuthActionState,
    formData: FormData,
  ) => Promise<AuthActionState>;
};

const INITIAL_STATE: AuthActionState = { error: null };

export function AuthForm({
  title,
  description,
  notice,
  submitLabel,
  alternateLabel,
  alternateHref,
  alternateText,
  fields,
  action,
}: AuthFormProps) {
  const [state, formAction, isPending] = useActionState(action, INITIAL_STATE);

  return (
    <section className="auth-shell">
      <div className="auth-panel auth-panel-copy">
        <p className="eyebrow">SpendFlow access</p>
        <h1>{title}</h1>
        <p className="hero-copy">{description}</p>
        <div className="auth-copy-grid">
          <article className="auth-copy-card">
            <strong>JWT-backed session</strong>
            <span>
              The frontend now stores the backend token in an httpOnly cookie and uses it for authenticated requests.
            </span>
          </article>
          <article className="auth-copy-card">
            <strong>Protected app routes</strong>
            <span>
              App pages require a session cookie before loading, while the backend still validates the JWT on every request.
            </span>
          </article>
        </div>
      </div>

      <div className="auth-panel auth-panel-form">
        <form action={formAction} className="auth-form-card">
          {notice ? <p className="auth-notice">{notice}</p> : null}

          {fields.map((field) => (
            <label key={field.name} className="auth-field">
              <span>
                {field.label}
                {field.optional ? " (optional)" : ""}
              </span>
              <input
                name={field.name}
                type={field.type}
                placeholder={field.placeholder}
                autoComplete={field.autoComplete}
                required={!field.optional}
              />
            </label>
          ))}

          {state.error ? <p className="auth-error">{state.error}</p> : null}

          <button type="submit" className="auth-submit" disabled={isPending}>
            {isPending ? "Submitting..." : submitLabel}
          </button>

          <p className="auth-switch">
            {alternateLabel} <Link href={alternateHref}>{alternateText}</Link>
          </p>
        </form>
      </div>
    </section>
  );
}
