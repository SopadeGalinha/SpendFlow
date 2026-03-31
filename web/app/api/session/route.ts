import { NextResponse } from "next/server";

import { SESSION_COOKIE_NAME } from "@/lib/auth-constants";
import { shouldUseSecureCookies } from "@/lib/auth";

const SESSION_COOKIE_MAX_AGE_SECONDS = 60 * 30;

type SessionRequestBody = {
  token?: string;
};

export async function POST(request: Request) {
  const body = (await request.json()) as SessionRequestBody;

  if (!body.token) {
    return NextResponse.json({ error: "Missing token." }, { status: 400 });
  }

  const response = NextResponse.json({ ok: true });
  response.cookies.set(SESSION_COOKIE_NAME, body.token, {
    httpOnly: true,
    sameSite: "lax",
    secure: await shouldUseSecureCookies(new Headers(request.headers)),
    path: "/",
    maxAge: SESSION_COOKIE_MAX_AGE_SECONDS,
  });

  return response;
}

export async function DELETE() {
  const response = NextResponse.json({ ok: true });
  response.cookies.delete(SESSION_COOKIE_NAME);
  return response;
}