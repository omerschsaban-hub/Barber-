import { engineeringOrigin } from './engineering-origin'

/**
 * Browser calls use the same-origin Next.js proxy. Server-side calls use one
 * canonical engineering origin so Vercel environment-variable drift cannot
 * silently route different API paths to different backends.
 */
export function backendUrl(path = ''): string {
  const normalized = path.replace(/^\//, '')
  if (typeof window !== 'undefined') return `/api/engineering/${normalized}`
  return `${engineeringOrigin()}/${normalized}`
}

function isRetryable(method: string, status?: number) {
  const safeMethod = ['GET', 'HEAD', 'OPTIONS'].includes(method.toUpperCase())
  return safeMethod && (status === undefined || status === 408 || status === 429 || status >= 500)
}

export async function backendFetch(path: string, init: RequestInit = {}): Promise<Response> {
  const headers = new Headers(init.headers)
  if (!headers.has('content-type') && init.body && !(init.body instanceof FormData)) {
    headers.set('content-type', 'application/json')
  }
  const requestId = headers.get('x-request-id') || crypto.randomUUID()
  headers.set('x-request-id', requestId)

  const method = init.method || 'GET'
  const attempts = isRetryable(method) ? 2 : 1
  let lastError: unknown

  for (let attempt = 0; attempt < attempts; attempt += 1) {
    const controller = new AbortController()
    const timeout = setTimeout(() => controller.abort(), 12_000)
    try {
      const response = await fetch(backendUrl(path), {
        ...init,
        headers,
        cache: 'no-store',
        signal: controller.signal,
      })
      if (attempt + 1 < attempts && isRetryable(method, response.status)) {
        await new Promise(resolve => setTimeout(resolve, 150 * (attempt + 1)))
        continue
      }
      return response
    } catch (error) {
      lastError = error
      if (attempt + 1 < attempts) {
        await new Promise(resolve => setTimeout(resolve, 150 * (attempt + 1)))
        continue
      }
    } finally {
      clearTimeout(timeout)
    }
  }

  throw lastError instanceof Error ? lastError : new Error('Backend request failed')
}

export function backendFailure(error: unknown, requestId?: string) {
  const message = error instanceof Error && error.name === 'AbortError' ? 'Backend request timed out' : 'Backend unavailable'
  return { error: message, request_id: requestId || undefined }
}
