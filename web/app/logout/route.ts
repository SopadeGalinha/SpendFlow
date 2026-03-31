import { NextResponse } from "next/server";

import { SESSION_COOKIE_NAME } from "@/lib/auth-constants";

export async function GET(request: Request) {
  const responseUrl = new URL("/login", request.url);

  const response = NextResponse.redirect(responseUrl);
  response.cookies.delete(SESSION_COOKIE_NAME);
  return response;
}
