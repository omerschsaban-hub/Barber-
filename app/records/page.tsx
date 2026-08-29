'use client';
import {useState} from 'react';
import {PDFDocument,StandardFonts,rgb} from 'pdf-lib';

const ENGINE='/api/engineering';

type Preview={filename:string;content_sha256:string;columns:{source_column:string;normalized:string;candidates:string[];status:string}[];row_count_preview:number;rows:Record<string,string>[];requires_confirmation:boolean};

export default function Records(){
  const [file,setFile]=useState<File>();
  const [preview,setPreview]=useState<Preview>();
  const [error,setError]=useState('');
  const [busy,setBusy]=useState(false);
  const [serial,setSerial]=useState('');
  const [gauge,setGauge]=useState('');
  const [machine,setMachine]=useState('');
  const [feature,setFeature]=useState('');
  const [nominal,setNominal]=useState<number>();
  const [measured,setMeasured]=useState<number>();

  async function inspect(){
    if(!file)return;
    setBusy(true);setError('');setPreview(undefined);
    try{
      const fd=new FormData();fd.append('file',file,file.name);
      const r=await fetch(`${ENGINE}/v1/import/preview`,{method:'POST',body:fd,signal:AbortSignal.timeout(30_000)});
      const j=await r.json().catch(()=>({detail:'Engineering service returned invalid JSON.'}));
      if(!r.ok)throw new Error(j.detail||`Import failed (${r.status})`);
      setPreview(j);
      const row=j.rows?.[0]||{};
      const value=(name:string)=>{const key=j.columns?.find((c:any)=>c.candidates?.includes(name))?.source_column;return key?row[key]:''};
      setSerial(value('serial'));setGauge('');setMachine(value('machine'));setFeature(value('feature'));
      const n=Number(value('nominal_mm'));const m=Number(value('measured_mm'));
      if(Number.isFinite(n))setNominal(n);if(Number.isFinite(m))setMeasured(m);
    }catch(e:any){setError(e?.name==='TimeoutError'?'The import took too long. No result was accepted.':(e?.message||'Import failed.'));}
    finally{setBusy(false)}
  }

  async function pdf(){
    if(!preview)return;
    const doc=await PDFDocument.create();const page=doc.addPage();const font=await doc.embedFont(StandardFonts.Courier);let y=760;
    const line=(s:string,b=false)=>{page.drawText(s.slice(0,110),{x:40,y,size:b?13:9,font,color:rgb(.9,.9,.9)});y-=b?24:16};
    line('FABRIENT — INSPECTION RECORD',true);line(`Source: ${preview.filename}`);line(`Rows previewed: ${preview.row_count_preview}`);line(`Serial: ${serial||'from source'}`);line(`Machine: ${machine||'from source'}`);line(`Feature: ${feature||'from source'}`);line(`Nominal: ${nominal ?? 'from source'}${nominal!==undefined?' mm':''}`);line(`Measured: ${measured ?? 'from source'}${measured!==undefined?' mm':''}`);line('Provenance: user-uploaded inspection evidence');
    const bytes=await doc.save();const url=URL.createObjectURL(new Blob([new Uint8Array(bytes)],{type:'application/pdf'}));const a=document.createElement('a');a.href=url;a.download=`inspection-${preview.filename.replace(/\.[^.]+$/,'')}.pdf`;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
  }

  function csv(){
    if(!preview)return;
    const headers=preview.columns.map(c=>c.source_column);const lines=[headers.map(csvCell).join(','),...preview.rows.map(row=>headers.map(h=>csvCell(row[h]??'')).join(','))];
    const blob=new Blob([lines.join('\n')],{type:'text/csv;charset=utf-8'});const url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download=`inspection-${preview.filename.replace(/\.[^.]+$/,'')}.csv`;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
  }

  return <main className="page">
    <div className="eyebrow">TRACEABILITY / INSPECTION RECORD</div>
    <h1 className="title">Bring the inspection data you already have.</h1>
    <p className="muted">Upload a CSV. Fabrient detects common columns and reuses the values instead of making you retype serials, machines, dates, dimensions, and measurements.</p>
    <section className="panel">
      <label className="dropzone"><input type="file" accept=".csv,text/csv" onChange={e=>setFile(e.target.files?.[0])}/><strong>{file?.name||'Choose inspection CSV'}</strong><span className="muted small">Fabrient reads the source; it does not invent measurements.</span></label>
      <button className="button primary" onClick={inspect} disabled={!file||busy}>{busy?'Reading…':'Read inspection data'}</button>
      {error&&<p className="error" role="alert">{error}</p>}
    </section>

    {preview&&<>
      <section className="panel" style={{marginTop:16}}>
        <div className="eyebrow">AUTO-DETECTED</div>
        <h2>{preview.row_count_preview} rows found</h2>
        <p className="muted">{preview.requires_confirmation?'A few columns need your review before they can be trusted.':'The columns are unambiguous and can be used as detected.'}</p>
        <div className="workspace-grid" style={{marginTop:12}}>{preview.columns.map(c=><div className="panel" key={c.source_column}><strong>{c.source_column}</strong><p className="muted small">{c.candidates.length===1?`Detected as ${c.candidates[0]}`:c.candidates.length?`Could be: ${c.candidates.join(', ')}`:'No known meaning detected'}</p></div>)}</div>
      </section>

      <section className="panel" style={{marginTop:16}}>
        <div className="eyebrow">OPTIONAL CORRECTIONS</div>
        <h2>Only correct what Fabrient could not infer.</h2>
        <div className="grid grid2">
          <label className="field">Machine<input value={machine} onChange={e=>setMachine(e.target.value)} placeholder="Auto-detected if present"/></label>
          <label className="field">Serial<input value={serial} onChange={e=>setSerial(e.target.value)} placeholder="Auto-detected if present"/></label>
          <label className="field">Feature<input value={feature} onChange={e=>setFeature(e.target.value)} placeholder="Auto-detected if present"/></label>
          <label className="field">Nominal (mm)<input type="number" value={nominal??''} onChange={e=>setNominal(e.target.value===''?undefined:Number(e.target.value))} placeholder="Auto-detected if present"/></label>
          <label className="field">Measured (mm)<input type="number" value={measured??''} onChange={e=>setMeasured(e.target.value===''?undefined:Number(e.target.value))} placeholder="Auto-detected if present"/></label>
          <label className="field">Gauge<input value={gauge} onChange={e=>setGauge(e.target.value)} placeholder="Optional"/></label>
        </div>
        <p className="muted small">These fields are corrections, not a required form. Source values remain the authoritative evidence unless you explicitly change the correction.</p>
        <button className="button primary" onClick={pdf}>Download PDF</button><button className="button" onClick={csv} style={{marginLeft:8}}>Download CSV</button>
      </section>
    </>}
  </main>
}

function csvCell(value:string){return `"${String(value).replace(/"/g,'""')}"`}
