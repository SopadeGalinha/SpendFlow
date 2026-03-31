import type { NextRequest } from "next/server";
import { NextResponse } from "next/server";

import { AUTH_ROUTES, SESSION_COOKIE_NAME } from "@/lib/auth-constants";

function isAuthDebugEnabled() {
  return (
    process.env.SPENDFLOW_DEBUG_AUTH === "true" ||
    process.env.NODE_ENV !== "production"
  );
}

function logAuthMiddleware(
  request: NextRequest,
  token: string | undefined,
  decision: string,
) {
  if (!isAuthDebugEnabled()) {
    return;
  }

  console.info("[spendflow-auth][middleware]", {
    decision,
    method: request.method,
    pathname: request.nextUrl.pathname,
    token: token ?? null,
    hasToken: Boolean(token),
    host:
      request.headers.get("x-forwarded-host") ??
      request.headers.get("host") ??
      null,
  });
}

function isAssetPath(pathname: string) {
  return (
    pathname.startsWith("/_next") ||
    pathname.startsWith("/favicon") ||
    pathname.includes(".")
  );
}

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  if (isAssetPath(pathname)) {
    logAuthMiddleware(request, undefined, "allow-asset");
    return NextResponse.next();
  }

  const token = request.cookies.get(SESSION_COOKIE_NAME)?.value;
  const isAuthRoute = AUTH_ROUTES.includes(pathname as (typeof AUTH_ROUTES)[number]);

  if (!token && !isAuthRoute) {
    logAuthMiddleware(request, token, "redirect-login-missing-token");
    return NextResponse.redirect(new URL("/login", request.url));
  }

  if (token && isAuthRoute) {
    logAuthMiddleware(request, token, "redirect-home-auth-route-with-token");
    return NextResponse.redirect(new URL("/", request.url));
  }

  logAuthMiddleware(request, token, "allow");

  return NextResponse.next();
}

export const config = {
  matcher: ["/((?!api).*)"],
};