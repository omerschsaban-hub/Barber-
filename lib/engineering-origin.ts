const DEFAULT_ENGINEERING_ORIGIN = 'https://fabrient-engineering.onrender.com'

/**
 * There is exactly one production engineering origin.
 * Browser requests stay same-origin through the Next.js proxy, so public
 * environment variables can never accidentally point a client at a different
 * backend. Server-side code uses FABRIENT_API_URL when explicitly configured,
 * otherwise the canonical Render service.
 */
export function engineeringOrigin(): string {
  const configured = process.env.FABRIENT_API_URL?.trim()
  const publicConfigured = process.env.NEXT_PUBLIC_ENGINEERING_API?.trim()
  const candidate = process.env.NODE_ENV === 'production'
    ? (configured || DEFAULT_ENGINEERING_ORIGIN)
    : (configured || publicConfigured || DEFAULT_ENGINEERING_ORIGIN)
  return candidate.replace(/\/$/, '')
}

export const CANONICAL_ENGINEERING_ORIGIN = DEFAULT_ENGINEERING_ORIGIN
