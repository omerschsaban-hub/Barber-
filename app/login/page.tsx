'use client';

import { FormEvent, useEffect, useRef, useState } from 'react';
import { createBrowserSupabase } from '@/lib/supabase-browser';

const RESEND_SECONDS = 60;

function safeRedirect(value: string | null) {
  if (!value || !value.startsWith('/') || value.startsWith('//')) return '/workspace';
  return value;
}

export default function Login() {
  const [email, setEmail] = useState('');
  const [code, setCode] = useState('');
  const [step, setStep] = useState<'email' | 'code'>('email');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [seconds, setSeconds] = useState(0);
  const codeRef = useRef<HTMLInputElement>(null);
  const redirect = typeof window !== 'undefined' ? safeRedirect(new URLSearchParams(window.location.search).get('redirect')) : '/workspace';

  const getSupabase = () => {
    const client = createBrowserSupabase();
    if (!client) {
      setError('Authentication is not configured.');
      return null;
    }
    return client;
  };

  useEffect(() => {
    if (!seconds) return;
    const id = setInterval(() => setSeconds((s) => Math.max(0, s - 1)), 1000);
    return () => clearInterval(id);
  }, [seconds]);

  useEffect(() => {
    if (step === 'code') codeRef.current?.focus();
  }, [step]);

  async function sendCode(e?: FormEvent) {
    e?.preventDefault();
    setError('');
    const normalized = email.trim().toLowerCase();
    if (!/^\S+@gmail\.com$/i.test(normalized)) {
      setError('Use your Gmail address.');
      return;
    }
    const supabase = getSupabase();
    if (!supabase) return;
    setBusy(true);
    try {
      const { error } = await supabase.auth.signInWithOtp({ email: normalized, options: { shouldCreateUser: true } });
      if (error) throw error;
      setEmail(normalized);
      setCode('');
      setStep('code');
      setSeconds(RESEND_SECONDS);
    } catch (err: any) {
      setError(err?.message || 'Could not send your code. Try again.');
    } finally {
      setBusy(false);
    }
  }

  async function verify(e?: FormEvent) {
    e?.preventDefault();
    if (code.length !== 6) return;
    setError('');
    const supabase = getSupabase();
    if (!supabase) return;
    setBusy(true);
    try {
      const { error } = await supabase.auth.verifyOtp({ email, token: code, type: 'email' });
      if (error) throw error;
      window.location.replace(redirect);
    } catch (err: any) {
      setError(err?.message || 'That code is invalid or expired.');
    } finally {
      setBusy(false);
    }
  }

  function onCode(value: string) {
    const clean = value.replace(/\D/g, '').slice(0, 6);
    setCode(clean);
    if (clean.length === 6) void verify();
  }

  function openGmail() {
    window.open('https://mail.google.com/', '_blank', 'noopener,noreferrer');
  }

  return (
    <main className="page auth-page">
      <div className="auth-card panel">
        <div className="auth-mark">F</div>
        <div className="eyebrow">FABRIENT / ACCESS</div>
        {step === 'email' ? (
          <>
            <h1 className="title">Get into Fabrient.</h1>
            <p className="muted">Enter Gmail and we’ll send one short code. No password and no inbox access.</p>
            <form onSubmit={sendCode}>
              <label>Gmail<input autoFocus inputMode="email" autoComplete="email" type="email" placeholder="you@gmail.com" value={email} onChange={(e) => setEmail(e.target.value)} /></label>
              <button className="button primary auth-submit" disabled={busy || !email.trim()}>{busy ? 'Sending…' : 'Send code'}</button>
            </form>
          </>
        ) : (
          <>
            <h1 className="title">Check Gmail.</h1>
            <p className="muted">Your six-digit code was sent to <strong>{email}</strong>.</p>
            <button className="button gmail-button" onClick={openGmail}>Open Gmail ↗</button>
            <form onSubmit={verify}>
              <label>6-digit code<input ref={codeRef} className="otp-input" inputMode="numeric" autoComplete="one-time-code" pattern="[0-9]*" maxLength={6} placeholder="123456" value={code} onChange={(e) => onCode(e.target.value)} /></label>
              <button className="button primary auth-submit" disabled={busy || code.length !== 6}>{busy ? 'Checking…' : 'Verify and continue'}</button>
            </form>
            <div className="auth-actions">
              <button className="link-button" onClick={() => { setStep('email'); setCode(''); setError(''); }}>Change email</button>
              {seconds > 0 ? <span className="muted">Resend in {seconds}s</span> : <button className="link-button" onClick={() => void sendCode()}>Resend code</button>}
            </div>
          </>
        )}
        {error && <p className="error" role="alert">{error}</p>}
        <p className="auth-footnote">Fabrient uses one Gmail OTP sign-in path. It never asks for Gmail inbox permissions.</p>
      </div>
    </main>
  );
}
