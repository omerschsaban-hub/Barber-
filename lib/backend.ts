const DEFAULT_API = 'https://fabrient-engineering.onrender.com'

export function backendUrl(path = ''): string {
  const base = (process.env.FABRIENT_API_URL || process.env.NEXT_PUBLIC_ENGINEERING_API || DEFAULT_API).replace(/\/$/, '')
  return `${base}/${path.replace(/^\//, '')}`
}

export async function backendFetch(path: string, init: RequestInit = {}): Promise<Response> {
  const headers = new Headers(init.headers)
  if (!headers.has('content-type') && init.body && !(init.body instanceof FormData)) {
    headers.set('content-type', 'application/json')
  }
  const requestId = headers.get('x-request-id') || crypto.randomUUID()
  headers.set('x-request-id', requestId)
  const controller = new AbortController()
  const timeout = setTimeout(() => controller.abort(), 20_000)
  try {
    return await fetch(backendUrl(path), { ...init, headers, cache: 'no-store', signal: controller.signal })
  } finally {
    clearTimeout(timeout)
  }
}

export function backendFailure(error: unknown, requestId?: string) {
  const message = error instanceof Error && error.name === 'AbortError' ? 'Backend request timed out' : 'Backend unavailable'
  return { error: message, request_id: requestId || undefined }
}
