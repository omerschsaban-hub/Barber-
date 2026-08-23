import {createClient, type SupabaseClient} from '@supabase/supabase-js'

const url = process.env.NEXT_PUBLIC_SUPABASE_URL
const key = process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY || process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY

let client: SupabaseClient | null = null

export function getSupabase(): SupabaseClient | null {
  if (client) return client
  if (!url || !key) return null
  try {
    client = createClient(url, key)
    return client
  } catch {
    return null
  }
}

export const supabaseConfigured = Boolean(url && key)
