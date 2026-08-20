'use client';

import {useState} from 'react';
import {Canvas} from '@react-three/fiber';
import {OrbitControls} from '@react-three/drei';

const ENGINE = process.env.NEXT_PUBLIC_ENGINEERING_API || 'http://localhost:8000';

function Box({d}:{d:number[]}) {
  const max = Math.max(...d, 0.001);
  const scale:[number,number,number] = [
    Math.max((d[0] ?? 0) / max * 4, .1),
    Math.max((d[1] ?? 0) / max * 4, .1),
    Math.max((d[2] ?? 0) / max * 4, .1),
  ];
  return <mesh scale={scale}>
    <boxGeometry args={[1,1,1]} />
    <meshStandardMaterial wireframe />
  </mesh>;
}

export default function Geometry() {
  const [file,setFile] = useState<File>();
  const [data,setData] = useState<any>();
  const [error,setError] = useState('');
  const [loading,setLoading] = useState(false);

  async function run() {
    if (!file) return;
    setError('');
    setLoading(true);
    try {
      const fd = new FormData();
      fd.append('file',file);
      const r = await fetch(`${ENGINE}/v1/geometry/step`,{method:'POST',body:fd});
      const j = await r.json();
      if (!r.ok) throw new Error(j.detail || 'Geometry extraction failed');
      setData(j);
    } finally {
      setLoading(false);
    }
  }

  const size = data?.bounding_box?.size;

  return <main className="page wide">
    <div className="eyebrow">GEOMETRY / STEP</div>
    <h1 className="title">Actual geometry context</h1>
    <p className="muted">Upload a STEP file. Fabrient extracts only geometry it can prove from the file and labels limited extraction instead of inventing BREP features.</p>
    <div className="workspace-grid">
      <section className="panel">
        <h2>STEP INPUT</h2>
        <input type="file" accept=".step,.stp" onChange={e=>setFile(e.target.files?.[0])}/>
        <button className="button primary" disabled={!file || loading} onClick={()=>run().catch(e=>setError(e.message))}>{loading ? 'Extracting…' : 'Extract geometry'}</button>
        {error&&<p className="error">{error}</p>}
        {data&&<>
          <p><strong>Status:</strong> {data.status}</p>
          <p className="muted">Topology verified: {String(data.provenance?.topology_verified ?? false)}</p>
          <pre className="provenance">{JSON.stringify(data,null,2)}</pre>
        </>}
      </section>
      <section className="panel">
        <h2>COMPUTED MODEL VIEW</h2>
        {size?.length === 3 ? <div className="viewer">
          <Canvas camera={{position:[5,4,5]}}>
            <ambientLight intensity={1}/><directionalLight position={[3,4,5]}/>
            <Box d={size}/><OrbitControls enableDamping/>
          </Canvas>
          <div className="viewer-label">{size.map((v:number)=>v.toFixed(3)).join(' × ')} {data.bounding_box.units}</div>
        </div> : <p className="muted">No verified bounding-box geometry has been extracted.</p>}
      </section>
    </div>
  </main>;
}
