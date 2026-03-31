import { NextResponse } from "next/server";

import { getApiBaseUrl, getSessionToken } from "@/lib/auth";

function buildAuthHeaders(token: string, contentType?: string) {
  const headers = new Headers({
    Authorization: `Bearer ${token}`,
  });

  if (contentType) {
    headers.set("Content-Type", contentType);
  }

  return headers;
}

async function parseErrorDetail(response: Response) {
  const fallback = "Unable to process user preference request.";

  try {
    const parsed = (await response.json()) as { detail?: string };
    return parsed.detail ?? fallback;
  } catch {
    return fallback;
  }
}

export async function GET() {
  const token = await getSessionToken();

  if (!token) {
    return NextResponse.json({ detail: "Unauthorized" }, { status: 401 });
  }

  const response = await fetch(`${getApiBaseUrl()}/api/v1/auth/preferences`, {
    method: "GET",
    headers: buildAuthHeaders(token),
    cache: "no-store",
  });

  if (!response.ok) {
    return NextResponse.json(
      { detail: await parseErrorDetail(response) },
      { status: response.status },
    );
  }

  const payload = (await response.json()) as unknown;
  return NextResponse.json(payload);
}

export async function PUT(request: Request) {
  const token = await getSessionToken();

  if (!token) {
    return NextResponse.json({ detail: "Unauthorized" }, { status: 401 });
  }

  const body = (await request.json()) as unknown;

  const response = await fetch(`${getApiBaseUrl()}/api/v1/auth/preferences`, {
    method: "PUT",
    headers: buildAuthHeaders(token, "application/json"),
    body: JSON.stringify(body),
    cache: "no-store",
  });

  if (!response.ok) {
    return NextResponse.json(
      { detail: await parseErrorDetail(response) },
      { status: response.status },
    );
  }

  const payload = (await response.json()) as unknown;
  return NextResponse.json(payload);
}
