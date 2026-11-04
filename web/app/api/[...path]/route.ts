import type { NextRequest } from "next/server";

// Next builds the rewrite table at build time, so a rewrite would fix the API address
// inside the image. This handler reads the address for each request instead.
const apiUrl = () => process.env.API_URL ?? "http://localhost:8000";

type Context = { params: Promise<{ path: string[] }> };

export const dynamic = "force-dynamic";

async function proxy(request: NextRequest, path: string[]) {
  const target = `${apiUrl()}/${path.join("/")}${request.nextUrl.search}`;
  const hasBody = request.method !== "GET" && request.method !== "HEAD";

  const upstream = await fetch(target, {
    method: request.method,
    headers: { "content-type": request.headers.get("content-type") ?? "application/json" },
    body: hasBody ? await request.text() : undefined,
    cache: "no-store",
  });

  // The body passes through unread, so a streamed answer reaches the browser as it arrives.
  return new Response(upstream.body, {
    status: upstream.status,
    headers: { "content-type": upstream.headers.get("content-type") ?? "application/json" },
  });
}

export async function GET(request: NextRequest, context: Context) {
  return proxy(request, (await context.params).path);
}

export async function POST(request: NextRequest, context: Context) {
  return proxy(request, (await context.params).path);
}
