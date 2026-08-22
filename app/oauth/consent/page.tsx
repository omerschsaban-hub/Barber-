'use client';

import { useEffect, useState } from 'react';
import { createBrowserSupabase } from '@/lib/supabase-browser';

type AuthorizationDetails = {
  authorization_id?: string;
  client?: { name?: string; client_id?: string };
  redirect_uri?: string;
  scope?: string;
};

const ALLOWED_SCOPES = new Set(['openid', 'email', 'profile']);

function getRequestedScope(data: unknown): string {
  if (!data || typeof data !== 'object') return '';
  const value = (data as { scope?: unknown }).scope;
  return typeof value === 'string' ? value : '';
}

export default function OAuthConsentPage() {
  const [details, setDetails] = useState<AuthorizationDetails | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    let cancelled = false;

    async function load() {
      const params = new URLSearchParams(window.location.search);
      const authorizationId = params.get('authorization_id');
      if (!authorizationId) {
        setError('This authorization request is missing its ID.');
        setLoading(false);
        return;
      }

      const supabase = createBrowserSupabase();
      if (!supabase) {
        setError('Authentication is not configured.');
        setLoading(false);
        return;
      }

      const { data: { user } } = await supabase.auth.getUser();
      if (!user) {
        window.location.replace(`/login?redirect=${encodeURIComponent(`/oauth/consent?authorization_id=${authorizationId}`)}`);
        return;
      }

      const { data, error: detailsError } = await supabase.auth.oauth.getAuthorizationDetails(authorizationId);
      if (cancelled) return;
      if (detailsError || !data) {
        setError(detailsError?.message || 'The authorization request is no longer valid.');
        setLoading(false);
        return;
      }

      const requestedScope = getRequestedScope(data);
      const requestedScopes = requestedScope.split(/\s+/).filter(Boolean);
      const unsupported = requestedScopes.filter((scope) => !ALLOWED_SCOPES.has(scope));
      if (unsupported.length) {
        setError(`This request asks for unsupported permissions: ${unsupported.join(', ')}.`);
        setLoading(false);
        return;
      }

      setDetails(data as AuthorizationDetails);
      setLoading(false);
    }

    void load();
    return () => { cancelled = true; };
  }, []);

  async function decide(decision: 'approve' | 'deny') {
    if (!details?.authorization_id) return;
    const supabase = createBrowserSupabase();
    if (!supabase) return;
    setBusy(true);
    setError('');

    const result = decision === 'approve'
      ? await supabase.auth.oauth.approveAuthorization(details.authorization_id)
      : await supabase.auth.oauth.denyAuthorization(details.authorization_id);

    if (result.error) {
      setError(result.error.message);
      setBusy(false);
      return;
    }

    window.location.assign(result.data.redirect_url);
  }

  if (loading) return <main className="page auth-page"><div className="auth-card panel"><p className="muted">Checking authorization request…</p></div></main>;

  const displayedScopes = getRequestedScope(details || '').split(/\s+/).filter(Boolean);

  return (
    <main className="page auth-page">
      <div className="auth-card panel">
        <div className="auth-mark">F</div>
        <div className="eyebrow">FABRIENT / AUTHORIZE</div>
        <h1 className="title">Connect Fabrient.</h1>
        {details ? (
          <>
            <p className="muted"><strong>{details.client?.name || 'An MCP client'}</strong> wants to connect to your Fabrient account.</p>
            <div className="panel" style={{ margin: '20px 0', padding: 16 }}>
              <p><strong>Permissions</strong></p>
              <ul>
                {(displayedScopes.length ? displayedScopes : ['email']).map((scope) => <li key={scope}>{scope}</li>)}
              </ul>
              <p className="muted">Fabrient does not grant Gmail inbox access. Your existing Gmail one-time-code login is used only to identify you.</p>
            </div>
            <div className="auth-actions">
              <button className="button primary" disabled={busy} onClick={() => void decide('approve')}>{busy ? 'Connecting…' : 'Allow connection'}</button>
              <button className="link-button" disabled={busy} onClick={() => void decide('deny')}>Cancel</button>
            </div>
          </>
        ) : <p className="error" role="alert">{error}</p>}
        {error && details && <p className="error" role="alert">{error}</p>}
      </div>
    </main>
  );
}
