import { NextRequest, NextResponse } from 'next/server';

const API = (process.env.FABRIENT_ENGINEERING_API || process.env.NEXT_PUBLIC_FABRIENT_ENGINEERING_API || 'http://localhost:8000').replace(/\/$/, '');

export async function GET(req: NextRequest, { params }: { params: Promise<{ action: string }> }) {
  const { action } = await params;
  const url = new URL(`${API}/integrations/${action}`);
  req.nextUrl.searchParams.forEach((value, key) => url.searchParams.set(key, value));
  return forward(url, { method: 'GET' });
}

export async function POST(req: NextRequest, { params }: { params: Promise<{ action: string }> }) {
  const { action } = await params;
  const body = await req.text();
  return forward(new URL(`${API}/integrations/${action}`), { method: 'POST', headers: { 'Content-Type': 'application/json' }, body });
}

async function forward(url: URL, init: RequestInit) {
  try {
    const response = await fetch(url, { ...init, cache: 'no-store' });
    const text = await response.text();
    return new NextResponse(text, { status: response.status, headers: { 'Content-Type': response.headers.get('content-type') || 'application/json' } });
  } catch {
    return NextResponse.json({ detail: 'Fabrient engineering API is unavailable' }, { status: 503 });
  }
}
