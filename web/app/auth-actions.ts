"use server";

import { redirect } from "next/navigation";

import {
  requestLogin,
  requestRegister,
  setSessionToken,
} from "@/lib/auth";

export type AuthActionState = {
  error: string | null;
};

export async function loginAction(
  _previousState: AuthActionState,
  formData: FormData,
): Promise<AuthActionState> {
  const email = String(formData.get("email") ?? "").trim();
  const password = String(formData.get("password") ?? "");

  if (!email || !password) {
    return { error: "Email and password are required." };
  }

  let token;
  try {
    token = await requestLogin(email, password);
  } catch (error) {
    return {
      error: error instanceof Error ? error.message : "Unable to sign in.",
    };
  }

  await setSessionToken(token.access_token);
  redirect("/");
}

export async function registerAction(
  _previousState: AuthActionState,
  formData: FormData,
): Promise<AuthActionState> {
  const username = String(formData.get("username") ?? "").trim();
  const email = String(formData.get("email") ?? "").trim();
  const password = String(formData.get("password") ?? "");
  const city = String(formData.get("city") ?? "").trim();

  if (!username || !email || !password) {
    return { error: "Username, email, and password are required." };
  }

  let token;
  try {
    await requestRegister({
      username,
      email,
      password,
      city,
      timezone: "UTC",
      currency: "EUR",
      default_weekend_adjustment: "keep",
    });
    token = await requestLogin(email, password);
  } catch (error) {
    return {
      error: error instanceof Error ? error.message : "Unable to register.",
    };
  }

  await setSessionToken(token.access_token);
  redirect("/");
}
