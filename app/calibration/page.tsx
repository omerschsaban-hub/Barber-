'use client';
import {useEffect, useMemo, useState} from 'react';

const ENGINE = '/api/engineering';
const PROFILE_KEY = 'fabrient-engineering-profile-v2';

type Profile = {
  nominal_mm: number;
  material: string;
  machine: string;
  process_temperature_c: number;
  ambient_temperature_c: number;
  shrinkage_pct: number;
  shrinkage_uncertainty_pct: number;
  tolerance_mm: number;
};

const DEFAULTS: Profile = {
  nominal_mm: 40,
  material: 'PETG',
  machine: 'Not set',
  process_temperature_c: 245,
  ambient_temperature_c: 23,
  shrinkage_pct: 0.5,
  shrinkage_uncertainty_pct: 0.15,
  tolerance_mm: 0.4,
};

export default function Calibration() {
  const [profile, setProfile] = useState<Profile>(DEFAULTS);
  const [advanced, setAdvanced] = useState(false);
  const [result, setResult] = useState<any>();
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    try {
      const raw = localStorage.getItem(PROFILE_KEY);
      if (raw) setProfile({...DEFAULTS, ...JSON.parse(raw)});
    } catch { /* keep safe defaults */ }
  }, []);

  useEffect(() => {
    try { localStorage.setItem(PROFILE_KEY, JSON.stringify(profile)); setSaved(true); } catch { /* persistence is optional */ }
  }, [profile]);

  function set<K extends keyof Profile>(key: K, value: Profile[K]) {
    setProfile(current => ({...current, [key]: value}));
  }

  async function run() {
    setBusy(true); setError(''); setResult(undefined);
    try {
      const p = profile;
      const r = await fetch(`${ENGINE}/v1/predict`, {
        method: 'POST',
        headers: {'content-type': 'application/json'},
        body: JSON.stringify({
          nominal_mm: p.nominal_mm,
          material: p.material,
          machine: p.machine,
          process_temperature_c: p.process_temperature_c,
          ambient_temperature_c: p.ambient_temperature_c,
          nominal_shrinkage_pct: p.shrinkage_pct,
          shrinkage_uncertainty_pct: p.shrinkage_uncertainty_pct,
          tolerance_lower_mm: -p.tolerance_mm / 2,
          tolerance_upper_mm: p.tolerance_mm / 2,
        }),
        signal: AbortSignal.timeout(120_000),
      });
      const j = await r.json().catch(() => ({detail: 'Engineering service returned invalid JSON.'}));
      if (!r.ok) throw new Error(j.detail || `Engineering request failed (${r.status})`);
      if (typeof j.prediction_mm !== 'number' || !Array.isArray(j.interval_95_mm)) {
        throw new Error('Engineering response is missing the prediction interval.');
      }
      setResult(j);
    } catch (e: any) {
      setError(e?.name === 'TimeoutError' ? 'The calculation took too long. No result was accepted.' : (e?.message || 'Unable to run the deterministic baseline.'));
    } finally { setBusy(false); }
  }

  const profileSummary = useMemo(() => `${profile.material} · ${profile.machine}`, [profile.material, profile.machine]);

  return <main className="page">
    <div className="eyebrow">MONITORING / CALIBRATION</div>
    <div className="workspace-head">
      <div>
        <h1 className="title">Physics first. Measurements decide.</h1>
        <p className="muted">Fabrient keeps the engineering controls, but remembers them so you do not repeatedly type the same numbers. Change them when you have better real information.</p>
      </div>
      <span className="status ok">{saved ? 'PROFILE SAVED' : 'DEFAULT PROFILE'}</span>
    </div>

    <section className="panel" style={{marginTop:20}}>
      <div className="eyebrow">READY TO RUN</div>
      <h2>{profileSummary}</h2>
      <p className="muted">Current baseline: {profile.nominal_mm} mm target, {profile.process_temperature_c}°C process, {profile.ambient_temperature_c}°C ambient, {profile.tolerance_mm} mm tolerance.</p>
      <button className="button primary" disabled={busy || profile.nominal_mm <= 0 || profile.shrinkage_uncertainty_pct < 0} onClick={run}>{busy ? 'Running…' : 'Run baseline'}</button>
      <button className="button" style={{marginLeft:8}} onClick={() => setAdvanced(v => !v)}>{advanced ? 'Hide technical inputs' : 'Adjust technical inputs'}</button>
    </section>

    {advanced && <section className="panel" style={{marginTop:14}}>
      <div className="eyebrow">ADVANCED / OPTIONAL</div>
      <p className="muted">These inputs remain available because better real values can improve accuracy. They are saved locally for the next run. Defaults are assumptions, not machine measurements.</p>
      <div className="grid grid2">
        <label className="field">Target dimension (mm)<input type="number" min="0.001" step="0.01" value={profile.nominal_mm} onChange={e=>set('nominal_mm', Number(e.target.value))}/></label>
        <label className="field">Material<input value={profile.material} onChange={e=>set('material', e.target.value)}/></label>
        <label className="field">Machine / printer<input value={profile.machine} onChange={e=>set('machine', e.target.value)}/></label>
        <label className="field">Process temperature (°C)<input type="number" step="1" value={profile.process_temperature_c} onChange={e=>set('process_temperature_c', Number(e.target.value))}/></label>
        <label className="field">Ambient temperature (°C)<input type="number" step="1" value={profile.ambient_temperature_c} onChange={e=>set('ambient_temperature_c', Number(e.target.value))}/></label>
        <label className="field">Expected shrinkage (%)<input type="number" step="0.01" value={profile.shrinkage_pct} onChange={e=>set('shrinkage_pct', Number(e.target.value))}/></label>
        <label className="field">Shrinkage uncertainty (%)<input type="number" min="0" step="0.01" value={profile.shrinkage_uncertainty_pct} onChange={e=>set('shrinkage_uncertainty_pct', Number(e.target.value))}/></label>
        <label className="field">Allowed tolerance (mm)<input type="number" min="0" step="0.01" value={profile.tolerance_mm} onChange={e=>set('tolerance_mm', Number(e.target.value))}/></label>
      </div>
    </section>}

    {error && <section className="panel" style={{marginTop:14}}><strong>We did not accept the result.</strong><p className="error">{error}</p></section>}

    <section className="panel" style={{marginTop:14}}>
      {result ? <>
        <div className="eyebrow">RESULT / {result.provenance?.version || 'deterministic'}</div>
        <div className="metric">{result.prediction_mm.toFixed(3)} mm</div>
        <p className="muted">95% interval: {result.interval_95_mm.map((x:number)=>x.toFixed(3)).join(' — ')} mm</p>
        <span className={`status ${result.status === 'pass' ? 'ok' : 'warn'}`}>{result.status}</span>
        <p className="annotation">This is a physics baseline, not a claim about your machine. Real observations remain required before calibration.</p>
        <details><summary>Show assumptions and evidence</summary><pre className="provenance">{JSON.stringify({inputs:profile,result}, null, 2)}</pre></details>
      </> : <><h2>No baseline yet</h2><p className="muted">Run the baseline with the saved profile, or open the advanced inputs if you have better real engineering data.</p></>}
    </section>
  </main>
}
