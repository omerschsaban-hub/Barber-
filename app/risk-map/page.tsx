'use client';

import {Canvas} from '@react-three/fiber';
import {OrbitControls, Edges} from '@react-three/drei';
import {useState} from 'react';

const ENGINE = process.env.NEXT_PUBLIC_ENGINEERING_API || 'http://localhost:8000';

function RiskMarker({position, score}: {position:[number,number,number]; score:number}) {
  const height = 0.35 + score * 1.15;
  return <group position={position}>
    <mesh position={[0,height/2,0]}>
      <cylinderGeometry args={[0.16,0.16,height,16]}/>
      <meshStandardMaterial color={score>=.8?'#ef4444':score>=.6?'#f59e0b':'#22c55e'} emissive={score>=.8?'#7f1d1d':score>=.6?'#78350f':'#14532d'} emissiveIntensity={.25}/>
    </mesh>
    <mesh position={[0,height+.08,0]}>
      <sphereGeometry args={[.18,16,16]}/>
      <meshStandardMaterial color={score>=.8?'#ef4444':score>=.6?'#f59e0b':'#22c55e'} emissive={score>=.8?'#7f1d1d':score>=.6?'#78350f':'#14532d'} emissiveIntensity={.4}/>
    </mesh>
  </group>;
}

function GeometryWithRisks({size,risks}:{size:number[]|null;risks:any[]}) {
  const d=size?.length===3?size:[6.4,2.2,4.1];
  const max=Math.max(...d,.001);
  const shape:[number,number,number]=[d[0]/max*6.4,d[1]/max*4.1,d[2]/max*4.1];
  return <>
    <ambientLight intensity={1.3}/><directionalLight position={[5,7,8]} intensity={2}/>
    <group rotation={[.08,-.25,0]}>
      <mesh>
        <boxGeometry args={shape}/>
        <meshStandardMaterial transparent opacity={.12} roughness={.7}/>
        <Edges linewidth={1.5}/>
      </mesh>
      {risks.slice(0,20).map((risk:any,index:number)=>{
        const p=Array.isArray(risk.position)&&risk.position.length===3?risk.position:[-shape[0]/2+(index%5)*shape[0]/4, -shape[1]/2+.05, -shape[2]/2+Math.floor(index/5)*shape[2]/4];
        return <RiskMarker key={risk.id||index} position={p as [number,number,number]} score={risk.risk_score}/>;
      })}
    </group>
    <gridHelper args={[12,12,'#334155','#1e293b']} position={[0,-shape[1]/2-.2,0]}/>
    <OrbitControls enableDamping makeDefault/>
  </>;
}

export default function RiskMap() {
  const [findings,setFindings]=useState('[{"id":"wall-1","category":"DFM","message":"Wall thickness below declared process limit","risk_score":0.82}]');
  const [sigma,setSigma]=useState(.1);
  const [tolerance,setTolerance]=useState(.4);
  const [result,setResult]=useState<any>();
  const [geometry,setGeometry]=useState<any>();
  const [file,setFile]=useState<File>();
  const [error,setError]=useState('');
  const [loading,setLoading]=useState(false);

  async function extractAndMap() {
    setError(''); setLoading(true);
    try {
      let geom=geometry;
      if(file){
        const fd=new FormData(); fd.append('file',file);
        const gr=await fetch(`${ENGINE}/v1/geometry/step`,{method:'POST',body:fd});
        const gj=await gr.json();
        if(!gr.ok) throw new Error(gj.detail||'STEP extraction failed');
        geom=gj; setGeometry(gj);
      }
      const parsed=JSON.parse(findings);
      if(!Array.isArray(parsed)) throw new Error('Findings must be a JSON array');
      const r=await fetch(`${ENGINE}/v1/risk-map`,{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({findings:parsed,uncertainty_sigma_mm:sigma,tolerance_mm:tolerance})});
      const body=await r.json();
      if(!r.ok) throw new Error(body.detail||'Risk map failed');
      setResult(body);
    } catch(e:any) { setError(e.message||'Risk map failed'); }
    finally { setLoading(false); }
  }

  const risks=result?.risk_map||[];
  const size=geometry?.bounding_box?.size||null;

  return <main className="page wide">
    <div className="eyebrow">ENGINEERING / RISK MAP</div>
    <h1 className="title">Evidence-backed risk map</h1>
    <p className="muted">Upload supplied STEP geometry, extract only kernel-proven geometry, then overlay deterministic risk findings. The visualization is not a physical acceptance decision.</p>

    <section className="panel" style={{marginTop:24,padding:0,overflow:'hidden'}}>
      <div style={{display:'flex',justifyContent:'space-between',alignItems:'center',padding:'18px 20px',borderBottom:'1px solid var(--border)'}}>
        <div><strong>3D GEOMETRY + RISK OVERLAY</strong><p className="muted" style={{margin:'4px 0 0'}}>{size?'Loaded from supplied STEP':'Upload a STEP to replace the preview'}</p></div>
        <span className="eyebrow">KERNEL CONTEXT</span>
      </div>
      <div style={{height:430,background:'#020617'}}>
        <Canvas camera={{position:[7.5,5.5,7.5],fov:42}}><GeometryWithRisks size={size} risks={risks}/></Canvas>
      </div>
      <div style={{display:'flex',gap:18,padding:'12px 20px',flexWrap:'wrap'}} className="muted">
        <span>● High risk</span><span>● Medium risk</span><span>● Lower risk</span>
        {size&&<span>STEP size: {size.map((v:number)=>v.toFixed(3)).join(' × ')}</span>}
      </div>
    </section>

    <div className="workspace-grid" style={{marginTop:24}}>
      <section className="panel">
        <h2>INPUT EVIDENCE</h2>
        <label>STEP file<input type="file" accept=".step,.stp" onChange={e=>setFile(e.target.files?.[0])}/></label>
        <label>Findings JSON<textarea rows={9} value={findings} onChange={e=>setFindings(e.target.value)}/></label>
        <label>Uncertainty σ (mm)<input type="number" step="0.001" value={sigma} onChange={e=>setSigma(+e.target.value)}/></label>
        <label>Tolerance band (mm)<input type="number" step="0.001" value={tolerance} onChange={e=>setTolerance(+e.target.value)}/></label>
        <button className="button primary" disabled={loading} onClick={extractAndMap}>{loading?'Extracting + mapping…':'Extract STEP + compute risk map'}</button>
        {error&&<p className="error">{error}</p>}
        {geometry&&<pre className="provenance">{JSON.stringify(geometry.provenance,null,2)}</pre>}
      </section>
      <section className="panel">
        <h2>RANKED RISKS</h2>
        {result?<>
          <div className="grid grid3">
            <div className="panel"><strong>{result.summary.critical}</strong><p className="muted">Critical</p></div>
            <div className="panel"><strong>{result.summary.high}</strong><p className="muted">High</p></div>
            <div className="panel"><strong>{result.summary.medium}</strong><p className="muted">Medium</p></div>
          </div>
          {risks.map((x:any)=><div className="panel" key={x.id}><strong>{x.level.toUpperCase()} · {x.category}</strong><p>{x.message}</p><p className="muted">Risk score: {x.risk_score.toFixed(3)} · Source: {x.source}</p></div>)}
          <pre className="provenance">{JSON.stringify(result.provenance,null,2)}</pre>
        </>:<p className="muted">No risk map yet.</p>}
      </section>
    </div>
  </main>;
}
