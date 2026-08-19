/** @type {import('next').NextConfig} */
const securityHeaders = [
  { key: 'X-Content-Type-Options', value: 'nosniff' },
  { key: 'Referrer-Policy', value: 'strict-origin-when-cross-origin' },
  { key: 'X-Frame-Options', value: 'DENY' },
  { key: 'Permissions-Policy', value: 'camera=(), microphone=(), geolocation=()' },
  { key: 'Strict-Transport-Security', value: 'max-age=31536000; includeSubDomains' },
  { key: 'Content-Security-Policy', value: "default-src 'self'; img-src 'self' data: blob: https:; font-src 'self' data: https:; style-src 'self' 'unsafe-inline'; script-src 'self' https://*.supabase.co; connect-src 'self' https://*.supabase.co https://api.openai.com; frame-ancestors 'none'; base-uri 'self'; form-action 'self'" }
]
const nextConfig = {
  reactStrictMode: true,
  poweredByHeader: false,
  async headers() { return [{ source: '/(.*)', headers: securityHeaders }] }
}
export default nextConfig
